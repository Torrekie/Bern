#import <AppKit/AppKit.h>
static NSString *reportPath;
static NSMutableArray *events;
static NSInteger actions=0;
static pid_t previousPID;
static void Record(NSString *kind, NSSlider *slider, NSEvent *event) {
    NSMutableDictionary *d=[@{@"kind":kind,@"time":@([NSDate timeIntervalSinceReferenceDate]),@"value":@(slider.doubleValue),@"actions":@(actions)} mutableCopy];
    if(event){d[@"eventType"]=@(event.type);d[@"point"]=NSStringFromPoint(event.locationInWindow);}
    [events addObject:d];
    NSDictionary *r=@{@"events":events,@"previousPID":@(previousPID),@"pid":@(getpid()),@"value":@(slider.doubleValue),@"actions":@(actions)};
    [[NSJSONSerialization dataWithJSONObject:r options:NSJSONWritingPrettyPrinted error:nil] writeToFile:reportPath atomically:YES];
}
@interface Slider : NSSlider @end
@implementation Slider
- (void)mouseDown:(NSEvent *)e { Record(@"mouseDown",self,e); [super mouseDown:e]; Record(@"mouseUp-return",self,nil); }
@end
@interface Owner : NSObject <NSApplicationDelegate>
@property NSWindow *window;
@property Slider *slider;
@end
@implementation Owner
- (void)action:(NSSlider *)sender { actions++; Record(@"action",sender,nil); }
- (void)applicationDidFinishLaunching:(NSNotification *)n {
    self.window=[[NSWindow alloc]initWithContentRect:NSMakeRect(400,300,480,180) styleMask:NSWindowStyleMaskTitled|NSWindowStyleMaskClosable backing:NSBackingStoreBuffered defer:NO];
    self.window.title=@"Bern native slider input probe";self.window.releasedWhenClosed=NO;self.window.restorable=NO;
    self.slider=[[Slider alloc]initWithFrame:NSMakeRect(40,75,400,30)];self.slider.minValue=0;self.slider.maxValue=100;self.slider.doubleValue=50;self.slider.continuous=YES;self.slider.target=self;self.slider.action=@selector(action:);[self.slider setAccessibilityLabel:@"Input probe volume"];[self.window.contentView addSubview:self.slider];
    [self.window orderFront:nil];Record(@"ready",self.slider,nil);
    [NSTimer scheduledTimerWithTimeInterval:90 repeats:NO block:^(NSTimer *timer){
        Record(@"complete",self.slider,nil);[self.window orderOut:nil];
        if(NSWorkspace.sharedWorkspace.frontmostApplication.processIdentifier==getpid())[[NSRunningApplication runningApplicationWithProcessIdentifier:previousPID]activateWithOptions:0];[NSApp terminate:nil];
    }];
}
@end
int main(int argc,const char **argv){@autoreleasepool{
    previousPID=NSWorkspace.sharedWorkspace.frontmostApplication.processIdentifier;
    reportPath=[NSString stringWithUTF8String:argv[1]];events=[NSMutableArray array];
    NSApplication *app=NSApplication.sharedApplication;[app setActivationPolicy:NSApplicationActivationPolicyAccessory];Owner *owner=[Owner new];app.delegate=owner;[app run];return 0;
}}
