// Shared media executor and presenters. All user gestures dispatch Bern media
// commands; AVFoundation observations report facts rather than issuing commands.
#import <AVFoundation/AVFoundation.h>
#import <QuartzCore/CAMetalLayer.h>
#if TARGET_OS_OSX
#import <CoreVideo/CoreVideo.h>
#endif

@class BNMediaAVPlayer, BNMediaSurface, BNMediaControlsView;
@interface BNMediaRuntime : NSObject
@property(nonatomic) BernApp *handle;
@property(nonatomic) BOOL kernel;
@property(nonatomic) uint64_t revision;
@property(nonatomic,strong) NSMutableDictionary<NSString *,BNMediaAVPlayer *> *executors;
@property(nonatomic,strong) NSDictionary<NSString *,NSDictionary *> *states;
@property(nonatomic,strong) NSMutableDictionary<NSString *,BNMediaSurface *> *surfaces;
@property(nonatomic,strong) NSMutableDictionary<NSString *,BNMediaControlsView *> *bars;
@property(nonatomic,strong) NSMutableDictionary<NSString *,NSString *> *owners;
@property(nonatomic,strong) NSMutableSet<NSString *> *seenSurfaces;
@property(nonatomic,strong) NSMutableDictionary<NSString *,id> *queryValues;
@property(nonatomic,strong) NSSet<NSString *> *logicalTokens;
@property(nonatomic,strong) NSSet<NSString *> *logicalQueries;
@property(nonatomic,strong) NSRecursiveLock *frameLock;
+(instancetype)shared;
-(BNMediaAVPlayer *)player:(NSString *)identifier;
-(void)complete:(uint64_t)request code:(NSString *)code message:(NSString *)message;
@end

static NSString *BNMediaText(NSString *key) {
    BNHost *host=[BNHost shared];
    for(NSDictionary *text in host.model[@"texts"]) if([text[@"key"] isEqual:key]) {
        NSDictionary *translations=text[@"translations"];
        return translations[host.language] ?: translations[host.model[@"languages"][@"default"]] ?: key;
    }
    return key;
}
static NSString *BNMediaTime(int64_t ms) {
    int64_t total=MAX(INT64_C(0),ms)/1000,h=total/3600,m=total%3600/60,s=total%60;
    return h ? [NSString stringWithFormat:@"%lld:%02lld:%02lld",(long long)h,(long long)m,(long long)s] : [NSString stringWithFormat:@"%lld:%02lld",(long long)m,(long long)s];
}
static NSString *BNMediaDescription(NSString *player) {
    NSDictionary *s=[BNMediaRuntime shared].states[player];
    if(!s) return @"";
    NSArray *phases=@[@"Idle",@"Loading",@"Ready",@"Playing",@"Paused",@"Buffering",@"Ended",@"Failed",@"Unavailable"];
    NSUInteger phase=[s[@"phase"] unsignedIntegerValue];
    return [NSString stringWithFormat:@"%@ %@ / %@",phase<phases.count?phases[phase]:@"Unavailable",BNMediaTime([s[@"position"] longLongValue]),BNIsNull(s[@"duration"])?@"--:--":BNMediaTime([s[@"duration"] longLongValue])];
}
static void BNMediaCommand(NSString *player, NSString *operation, NSArray *args) {
    BNMediaRuntime *runtime=[BNMediaRuntime shared]; if(!runtime.handle) return;
    NSDictionary *commands=@{@"open":@2,@"play":@3,@"pause":@4,@"seek":@5,@"set_volume":@6,@"set_muted":@7};
    NSNumber *command=commands[operation]; if(!command) BNThrow(@"unknown_command",@"Unknown media command");
    BNWriter *writer=[BNWriter new]; [writer text:player];
    if(command.unsignedIntValue==2) {
        id source=BNAt(args,0); if([source isKindOfClass:[NSArray class]]) source=BNAt(source,0);
        [writer text:BNString(source)];
    } else if(command.unsignedIntValue==5) [writer u64:(uint64_t)[BNAt(args,0) longLongValue]];
    else if(command.unsignedIntValue==6) [writer f64:[BNAt(args,0) doubleValue]];
    else if(command.unsignedIntValue==7) [writer u8:[BNAt(args,0) boolValue]?1:0];
    BNHost *host=[BNHost shared]; uint64_t token=host.nextToken++;
    bern_media_dispatch(runtime.handle,command.unsignedIntValue,writer.data.bytes,writer.data.length,token);
}

@interface BNMediaAVPlayer : NSObject
@property(nonatomic,strong) NSString *identifier;
@property(nonatomic,strong) AVPlayer *player;
@property(nonatomic,strong) AVPlayerItem *observedItem;
@property(nonatomic,strong) id timeObserver;
@property(nonatomic,strong) id endObserver;
@property(nonatomic,strong) id jumpObserver;
@property(nonatomic) uint64_t version;
@property(nonatomic) BOOL ended;
@property(nonatomic) BOOL started;
@property(nonatomic) BOOL observing;
-(instancetype)initWithIdentifier:(NSString *)identifier;
-(void)load:(NSURL *)url version:(uint64_t)version;
-(void)unload:(uint64_t)version;
-(void)report;
-(void)reset;
-(void)stop;
@end
@implementation BNMediaAVPlayer
-(instancetype)initWithIdentifier:(NSString *)identifier {
    if((self=[super init])) {
        _identifier=identifier;_player=[AVPlayer new];_player.actionAtItemEnd=AVPlayerActionAtItemEndPause;
        _player.preventsDisplaySleepDuringVideoPlayback=YES;
        for(NSString *key in @[@"timeControlStatus",@"volume",@"muted"]) [_player addObserver:self forKeyPath:key options:0 context:NULL];
        _observing=YES;
        __weak BNMediaAVPlayer *weak=self;
        _timeObserver=[_player addPeriodicTimeObserverForInterval:CMTimeMake(1,2) queue:dispatch_get_main_queue() usingBlock:^(CMTime time){ [weak report]; }];
    } return self;
}
-(void)observeValueForKeyPath:(NSString *)path ofObject:(id)object change:(NSDictionary *)change context:(void *)context {
    __weak BNMediaAVPlayer *weak=self;uint64_t version=_version;
    dispatch_async(dispatch_get_main_queue(), ^{ BNMediaAVPlayer *strong=weak;if(strong && strong.version==version)[strong report]; });
}
-(void)reset {
    if(_observedItem) { for(NSString *key in @[@"status",@"duration"]) [_observedItem removeObserver:self forKeyPath:key];_observedItem=nil; }
    if(_endObserver) [[NSNotificationCenter defaultCenter] removeObserver:_endObserver];_endObserver=nil;
    if(_jumpObserver) [[NSNotificationCenter defaultCenter] removeObserver:_jumpObserver];_jumpObserver=nil;
    _ended=NO;_started=NO;
}
-(void)load:(NSURL *)url version:(uint64_t)version {
    _version=version;[self reset];[_player pause];
    AVPlayerItem *item=[AVPlayerItem playerItemWithURL:url];_observedItem=item;
    for(NSString *key in @[@"status",@"duration"]) [item addObserver:self forKeyPath:key options:0 context:NULL];
    __weak BNMediaAVPlayer *weak=self;
    _endObserver=[[NSNotificationCenter defaultCenter] addObserverForName:AVPlayerItemDidPlayToEndTimeNotification object:item queue:[NSOperationQueue mainQueue] usingBlock:^(NSNotification *note){BNMediaAVPlayer *strong=weak;if(strong && strong.version==version){strong.ended=YES;[strong report];}}];
    _jumpObserver=[[NSNotificationCenter defaultCenter] addObserverForName:AVPlayerItemTimeJumpedNotification object:item queue:[NSOperationQueue mainQueue] usingBlock:^(NSNotification *note){BNMediaAVPlayer *strong=weak;if(strong && strong.version==version && strong.ended){double duration=CMTimeGetSeconds(item.duration),current=CMTimeGetSeconds(strong.player.currentTime);if(isfinite(duration)&&isfinite(current)&&current<duration-0.25){strong.ended=NO;[strong report];}}}];
    [_player replaceCurrentItemWithPlayerItem:item];[self report];
}
-(void)unload:(uint64_t)version { _version=version;[self reset];[_player pause];[_player replaceCurrentItemWithPlayerItem:nil];[self report]; }
-(void)report {
    BNMediaRuntime *runtime=[BNMediaRuntime shared];if(!runtime.handle)return;
    AVPlayerItem *item=_player.currentItem;uint32_t phase=0;NSString *error=nil;NSNumber *duration=nil;
    if(item) {
        CMTime value=item.duration;double seconds=CMTimeGetSeconds(value);
        if(CMTIME_IS_NUMERIC(value)&&isfinite(seconds)&&seconds>=0&&seconds<INT64_MAX/1000.0)duration=@((int64_t)llround(seconds*1000));
        if(item.status==AVPlayerItemStatusFailed){phase=7;error=item.error.localizedDescription;}
        else if(item.status==AVPlayerItemStatusUnknown)phase=1;
        else if(_ended)phase=6;
        else if(_player.timeControlStatus==AVPlayerTimeControlStatusPlaying){_started=YES;phase=3;}
        else if(_player.timeControlStatus==AVPlayerTimeControlStatusWaitingToPlayAtSpecifiedRate)phase=5;
        else phase=_started?4:2;
    }
    double seconds=CMTimeGetSeconds(_player.currentTime);int64_t position=isfinite(seconds)&&seconds<INT64_MAX/1000.0?(int64_t)llround(MAX(0,seconds)*1000):0;
    BNWriter *writer=[BNWriter new];[writer text:_identifier];[writer u64:_version];[writer u32:phase];[writer u64:(uint64_t)position];
    [writer u8:duration?1:0];if(duration)[writer u64:(uint64_t)duration.longLongValue];
    [writer u8:duration&&item.seekableTimeRanges.count?1:0];[writer f64:round((double)_player.volume*1000)/1000];[writer u8:_player.muted?1:0];
    [writer u8:error?1:0];if(error)[writer text:error];
    bern_media_event(runtime.handle,writer.data.bytes,writer.data.length);
}
-(void)stop {
    [self reset];[_player pause];[_player replaceCurrentItemWithPlayerItem:nil];
    if(_timeObserver){[_player removeTimeObserver:_timeObserver];_timeObserver=nil;}
    if(_observing){for(NSString *key in @[@"timeControlStatus",@"volume",@"muted"]) [_player removeObserver:self forKeyPath:key];_observing=NO;}
}
-(void)dealloc { [self stop]; }
@end

@implementation BNMediaRuntime
+(instancetype)shared {static BNMediaRuntime *runtime;static dispatch_once_t once;dispatch_once(&once, ^{runtime=[BNMediaRuntime new];runtime.executors=[NSMutableDictionary dictionary];runtime.states=@{};runtime.surfaces=[NSMutableDictionary dictionary];runtime.bars=[NSMutableDictionary dictionary];runtime.owners=[NSMutableDictionary dictionary];runtime.seenSurfaces=[NSMutableSet set];runtime.queryValues=[NSMutableDictionary dictionary];runtime.frameLock=[NSRecursiveLock new];});return runtime;}
-(BNMediaAVPlayer *)player:(NSString *)identifier {
    BNMediaAVPlayer *player=_executors[identifier];if(!player){
#if !TARGET_OS_OSX
        if(!_executors.count){AVAudioSession *session=[AVAudioSession sharedInstance];[session setCategory:AVAudioSessionCategoryPlayback mode:AVAudioSessionModeMoviePlayback options:0 error:NULL];[session setActive:YES error:NULL];}
#endif
        player=[[BNMediaAVPlayer alloc]initWithIdentifier:identifier];_executors[identifier]=player;
    }return player;
}
-(void)complete:(uint64_t)request code:(NSString *)code message:(NSString *)message {
    if(!_handle)return;BNWriter *writer=[BNWriter new];[writer u64:request];[writer u8:code?1:0];if(code){[writer text:code];[writer text:message?:@""];}
    bern_media_complete(_handle,writer.data.bytes,writer.data.length);
}
@end

#if !TARGET_OS_OSX
@interface BNMediaClock : NSObject
@property(nonatomic,strong) NSThread *thread;
+(instancetype)shared;
-(void)add:(CADisplayLink *)link;
-(void)remove:(CADisplayLink *)link;
@end
@implementation BNMediaClock
+(instancetype)shared {static BNMediaClock *clock;static dispatch_once_t once;dispatch_once(&once, ^{clock=[BNMediaClock new];clock.thread=[[NSThread alloc]initWithTarget:clock selector:@selector(run) object:nil];clock.thread.name=@"Bern media frames";clock.thread.qualityOfService=NSQualityOfServiceUserInteractive;[clock.thread start];});return clock;}
-(void)run {@autoreleasepool {[[NSRunLoop currentRunLoop]addPort:[NSMachPort port] forMode:NSDefaultRunLoopMode];while(![NSThread currentThread].cancelled){@autoreleasepool {[[NSRunLoop currentRunLoop]runMode:NSDefaultRunLoopMode beforeDate:[NSDate distantFuture]];}}}}
-(void)add:(CADisplayLink *)link {[link addToRunLoop:[NSRunLoop currentRunLoop] forMode:NSRunLoopCommonModes];}
-(void)remove:(CADisplayLink *)link {[link invalidate];}
@end
#endif

@interface BNMediaSurface : BNView
@property(nonatomic,strong) NSString *playerID;
@property(nonatomic,strong) NSString *token;
@property(nonatomic,strong) NSString *owner;
@property(nonatomic,strong) CALayer *picture;
@property(nonatomic,strong) BNView *status;
@property(nonatomic) BOOL attached;
@property(nonatomic) BOOL visible;
@property(nonatomic) uint32_t fit;
@property(nonatomic) CGFloat corner;
@property(nonatomic) CGSize lastPixels;
@property(nonatomic) CGFloat lastScale;
#if TARGET_OS_OSX
@property(nonatomic) CVDisplayLinkRef clock;
#else
@property(nonatomic,strong) CADisplayLink *clock;
#endif
-(void)update;
-(void)resize;
-(void)detach;
-(void)frame:(double)now target:(double)target;
@end
#if TARGET_OS_OSX
static CVReturn BNMediaFrame(CVDisplayLinkRef link,const CVTimeStamp *now,const CVTimeStamp *target,CVOptionFlags input,CVOptionFlags *output,void *context) {
    @autoreleasepool {BNMediaSurface *surface=(__bridge BNMediaSurface *)context;double frequency=CVGetHostClockFrequency();double current=(now->flags&kCVTimeStampHostTimeValid)?now->hostTime/frequency:CACurrentMediaTime();double next=(target->flags&kCVTimeStampHostTimeValid)?target->hostTime/frequency:current+1.0/60.0;[surface frame:current target:next];}return kCVReturnSuccess;
}
#endif
@implementation BNMediaSurface
-(instancetype)initWithFrame:(CGRect)frame {
    if((self=[super initWithFrame:frame])) {
#if TARGET_OS_OSX
        self.wantsLayer=YES;NSTextField *label=[NSTextField wrappingLabelWithString:@""];label.alignment=NSTextAlignmentCenter;label.textColor=NSColor.secondaryLabelColor;label.font=[NSFont systemFontOfSize:NSFont.smallSystemFontSize];_status=label;
#else
        UILabel *label=[UILabel new];label.numberOfLines=0;label.textAlignment=NSTextAlignmentCenter;label.textColor=UIColor.secondaryLabelColor;label.font=[UIFont preferredFontForTextStyle:UIFontTextStyleCaption1];_status=label;
#endif
        self.layer.backgroundColor=BNColor.blackColor.CGColor;[self addSubview:_status];
    }return self;
}
#if TARGET_OS_OSX
-(BOOL)isFlipped{return YES;}
-(void)layout{[super layout];[self resize];}
-(void)viewDidChangeBackingProperties{[super viewDidChangeBackingProperties];[self resize];}
-(void)viewDidMoveToWindow{[super viewDidMoveToWindow];[self resize];}
#else
-(void)layoutSubviews{[super layoutSubviews];[self resize];}
-(void)didMoveToWindow{[super didMoveToWindow];[self resize];}
-(void)step:(CADisplayLink *)link{[self frame:link.timestamp target:link.targetTimestamp];}
#endif
-(CGSize)intrinsicContentSize{return CGSizeMake(320,180);}
-(void)frame:(double)now target:(double)target {
    BNMediaRuntime *runtime=[BNMediaRuntime shared];[runtime.frameLock lock];
    if(_attached&&runtime.handle&&runtime.kernel){NSData *token=[_token dataUsingEncoding:NSUTF8StringEncoding];bern_media_surface_frame(runtime.handle,token.bytes,token.length,now,target);}
    [runtime.frameLock unlock];
}
-(void)resize {
    [CATransaction begin];[CATransaction setDisableActions:YES];_picture.frame=self.bounds;self.layer.cornerRadius=_corner;self.layer.masksToBounds=YES;_picture.cornerRadius=_corner;_picture.masksToBounds=YES;[CATransaction commit];
    _status.frame=CGRectInset(self.bounds,12,12);
    BNMediaRuntime *runtime=[BNMediaRuntime shared];if(!runtime.handle||!_visible)return;
#if TARGET_OS_OSX
    CGFloat scale=self.window.backingScaleFactor?:1;
#else
    CGFloat scale=self.window.screen.scale?:UIScreen.mainScreen.scale;
#endif
    // ScaleBox works in fixed logical units. The kernel receives physical
    // pixels after all ancestor transforms, as the SwiftUI sceneScale did.
    for(CALayer *ancestor=self.layer;ancestor;ancestor=ancestor.superlayer){CATransform3D transform=ancestor.transform;double factor=MAX(hypot(hypot(transform.m11,transform.m12),transform.m13),hypot(hypot(transform.m21,transform.m22),transform.m23));if(isfinite(factor)&&factor>0)scale*=factor;}
    CGSize pixels=CGSizeMake(MAX(1,round(self.bounds.size.width*scale)),MAX(1,round(self.bounds.size.height*scale)));
    if(runtime.kernel){CAMetalLayer *layer=(CAMetalLayer *)_picture;layer.drawableSize=pixels;layer.contentsScale=scale;}
    if(!_attached) {
        BNWriter *view=[BNWriter new];[view text:_token];[view u8:1];[view text:_playerID];[view text:_owner];bern_media_view(runtime.handle,view.data.bytes,view.data.length);
        if(runtime.kernel){BNWriter *writer=[BNWriter new];[writer text:_token];[writer text:_playerID];[writer u32:0];[writer u64:(uint64_t)(uintptr_t)(__bridge void *)_picture];[writer u32:(uint32_t)pixels.width];[writer u32:(uint32_t)pixels.height];[writer f64:scale];[writer u32:_fit];bern_media_surface_attach(runtime.handle,writer.data.bytes,writer.data.length);}
        [runtime.frameLock lock];_attached=YES;[runtime.frameLock unlock];
        if(runtime.kernel){
#if TARGET_OS_OSX
            CVDisplayLinkRef link=NULL;if(CVDisplayLinkCreateWithActiveCGDisplays(&link)==kCVReturnSuccess){_clock=link;NSNumber *screen=self.window.screen.deviceDescription[@"NSScreenNumber"];if(screen)CVDisplayLinkSetCurrentCGDisplay(link,screen.unsignedIntValue);CVDisplayLinkSetOutputCallback(link,BNMediaFrame,(__bridge void *)self);CVDisplayLinkStart(link);}else [[BNHost shared]showError:@"The media kernel's display clock could not start."];
#else
            _clock=[CADisplayLink displayLinkWithTarget:self selector:@selector(step:)];BNMediaClock *clock=[BNMediaClock shared];[clock performSelector:@selector(add:) onThread:clock.thread withObject:_clock waitUntilDone:NO];
#endif
        }
    } else if(runtime.kernel&&(!CGSizeEqualToSize(_lastPixels,pixels)||_lastScale!=scale)) {
        BNWriter *writer=[BNWriter new];[writer text:_token];[writer u32:(uint32_t)pixels.width];[writer u32:(uint32_t)pixels.height];[writer f64:scale];bern_media_surface_resize(runtime.handle,writer.data.bytes,writer.data.length);
    }
    _lastPixels=pixels;_lastScale=scale;
#if TARGET_OS_OSX
    if(_clock){NSNumber *screen=self.window.screen.deviceDescription[@"NSScreenNumber"];if(screen)CVDisplayLinkSetCurrentCGDisplay(_clock,screen.unsignedIntValue);}
#endif
}
-(void)update {
    BNMediaRuntime *runtime=[BNMediaRuntime shared];
    if(!_picture){_picture=runtime.kernel?[CAMetalLayer layer]:[AVPlayerLayer layer];[self.layer insertSublayer:_picture atIndex:0];}
    if(!runtime.kernel){AVPlayerLayer *layer=(AVPlayerLayer *)_picture;layer.player=[runtime player:_playerID].player;layer.videoGravity=_fit==1?AVLayerVideoGravityResizeAspectFill:_fit==2?AVLayerVideoGravityResize:AVLayerVideoGravityResizeAspect;}
    NSDictionary *state=runtime.states[_playerID];NSUInteger phase=state?[state[@"phase"] unsignedIntegerValue]:8;BOOL visible=phase>=2&&phase<=6;_picture.hidden=!visible;
    NSString *status=phase==7?[NSString stringWithFormat:@"%@\n%@",BNMediaText(@"bern.media.failed"),BNString(state[@"error"])]:phase==0?BNMediaText(@"bern.media.empty"):phase==1?BNMediaText(@"bern.query.loading"):visible?@"":BNMediaText(@"bern.media.unavailable");
#if TARGET_OS_OSX
    ((NSTextField *)_status).stringValue=status;self.accessibilityValue=BNMediaDescription(_playerID);
#else
    ((UILabel *)_status).text=status;self.accessibilityValue=BNMediaDescription(_playerID);
#endif
    [self resize];
}
-(void)detach {
    BNMediaRuntime *runtime=[BNMediaRuntime shared];[runtime.frameLock lock];BOOL wasAttached=_attached;_attached=NO;[runtime.frameLock unlock];
#if TARGET_OS_OSX
    if(_clock){CVDisplayLinkStop(_clock);CVDisplayLinkRelease(_clock);_clock=NULL;}
#else
    if(_clock){BNMediaClock *clock=[BNMediaClock shared];[clock performSelector:@selector(remove:) onThread:clock.thread withObject:_clock waitUntilDone:NO];_clock=nil;}
#endif
    if(wasAttached&&runtime.handle){BNWriter *writer=[BNWriter new];[writer text:_token];if(runtime.kernel)bern_media_surface_detach(runtime.handle,writer.data.bytes,writer.data.length);[writer u8:0];bern_media_view(runtime.handle,writer.data.bytes,writer.data.length);}
    if(!runtime.kernel)((AVPlayerLayer *)_picture).player=nil;
}
@end
static void BNMediaResizeTree(BNView *view) { if([view isKindOfClass:BNMediaSurface.class])[(BNMediaSurface *)view resize];else for(BNView *child in view.subviews)BNMediaResizeTree(child); }

#if TARGET_OS_OSX
@interface BNMediaSlider:NSSlider
@property(nonatomic)BOOL tracking;
@property(nonatomic,copy)void(^commit)(void);
@end
@implementation BNMediaSlider
-(void)mouseDown:(NSEvent *)event{_tracking=YES;[super mouseDown:event];_tracking=NO;if(_commit)_commit();}
@end
#endif
@interface BNMediaControlsView:BNView
@property(nonatomic,strong)NSString *playerID;
@property(nonatomic,strong)NSString *owner;
@property(nonatomic,strong)BNView *playButton;
@property(nonatomic,strong)BNView *muteButton;
@property(nonatomic,strong)BNView *position;
@property(nonatomic,strong)BNView *volume;
@property(nonatomic,strong)BNView *elapsed;
@property(nonatomic,strong)BNView *duration;
@property(nonatomic)BOOL seeking;
@property(nonatomic)BOOL settingVolume;
@property(nonatomic,strong)NSArray<BNControl *> *controls;
-(void)update;
-(void)play;
-(void)mute;
-(void)seek:(id)sender;
-(void)changeVolume:(id)sender;
-(void)seekCommit;
-(void)volumeCommit;
@end
@implementation BNMediaControlsView
-(instancetype)initWithFrame:(CGRect)frame {
    if((self=[super initWithFrame:frame])){
#if TARGET_OS_OSX
        NSButton *play=[NSButton buttonWithTitle:@"" target:self action:@selector(play)];play.bordered=NO;_playButton=play;NSButton *mute=[NSButton buttonWithTitle:@"" target:self action:@selector(mute)];mute.bordered=NO;_muteButton=mute;
        BNMediaSlider *position=[BNMediaSlider new];position.minValue=0;position.maxValue=1;position.continuous=YES;position.target=self;position.action=@selector(seek:);_position=position;
        BNMediaSlider *volume=[BNMediaSlider new];volume.minValue=0;volume.maxValue=1;volume.continuous=YES;volume.target=self;volume.action=@selector(changeVolume:);_volume=volume;
        __weak BNMediaControlsView *weak=self;position.commit=^{[weak seekCommit];};volume.commit=^{[weak volumeCommit];};
        NSTextField *elapsed=[NSTextField labelWithString:@"0:00"],*duration=[NSTextField labelWithString:@"--:--"];elapsed.textColor=duration.textColor=NSColor.secondaryLabelColor;elapsed.font=duration.font=[NSFont monospacedDigitSystemFontOfSize:NSFont.smallSystemFontSize weight:NSFontWeightRegular];_elapsed=elapsed;_duration=duration;
#else
        UIButton *play=[UIButton buttonWithType:UIButtonTypeSystem];[play addTarget:self action:@selector(play) forControlEvents:UIControlEventTouchUpInside];_playButton=play;UIButton *mute=[UIButton buttonWithType:UIButtonTypeSystem];[mute addTarget:self action:@selector(mute) forControlEvents:UIControlEventTouchUpInside];_muteButton=mute;
        UISlider *position=[UISlider new];[position addTarget:self action:@selector(seekStart) forControlEvents:UIControlEventTouchDown];[position addTarget:self action:@selector(seek:) forControlEvents:UIControlEventValueChanged];[position addTarget:self action:@selector(seekCommit) forControlEvents:UIControlEventTouchUpInside|UIControlEventTouchUpOutside|UIControlEventTouchCancel];_position=position;
        UISlider *volume=[UISlider new];[volume addTarget:self action:@selector(volumeStart) forControlEvents:UIControlEventTouchDown];[volume addTarget:self action:@selector(changeVolume:) forControlEvents:UIControlEventValueChanged];[volume addTarget:self action:@selector(volumeCommit) forControlEvents:UIControlEventTouchUpInside|UIControlEventTouchUpOutside|UIControlEventTouchCancel];_volume=volume;
        UILabel *elapsed=[UILabel new],*duration=[UILabel new];elapsed.textColor=duration.textColor=UIColor.secondaryLabelColor;elapsed.font=duration.font=[UIFont monospacedDigitSystemFontOfSize:12 weight:UIFontWeightRegular];_elapsed=elapsed;_duration=duration;
#endif
        for(BNView *view in @[_playButton,_elapsed,_position,_duration,_muteButton,_volume])[self addSubview:view];
    }return self;
}
-(CGSize)intrinsicContentSize{return CGSizeMake(440,30);}
#if TARGET_OS_OSX
-(BOOL)isFlipped{return YES;}
-(void)layout{[super layout];[self arrange];}
#else
-(void)layoutSubviews{[super layoutSubviews];[self arrange];}
-(void)seekStart{_seeking=YES;}
-(void)volumeStart{_settingVolume=YES;}
#endif
-(void)arrange{CGFloat width=self.bounds.size.width,height=self.bounds.size.height;CGFloat fixed=28+48+48+28+80+50;CGFloat seek=MAX(20,width-fixed),x=0;NSArray *views=@[_playButton,_elapsed,_position,_duration,_muteButton,_volume];CGFloat sizes[]={28,48,seek,48,28,80};for(NSUInteger i=0;i<views.count;i++){((BNView *)views[i]).frame=CGRectMake(x,0,sizes[i],height);x+=sizes[i]+10;}}
-(void)play{NSDictionary *s=[BNMediaRuntime shared].states[_playerID];NSUInteger phase=[s[@"phase"] unsignedIntegerValue];BNMediaCommand(_playerID,phase==3||phase==5?@"pause":@"play",@[]);}
-(void)mute{BNMediaCommand(_playerID,@"set_muted",@[@(![[BNMediaRuntime shared].states[_playerID][@"muted"] boolValue])]);}
-(double)positionValue{
#if TARGET_OS_OSX
    return ((NSSlider *)_position).doubleValue;
#else
    return ((UISlider *)_position).value;
#endif
}
-(double)volumeValue{
#if TARGET_OS_OSX
    return ((NSSlider *)_volume).doubleValue;
#else
    return ((UISlider *)_volume).value;
#endif
}
-(void)seek:(id)sender{
#if TARGET_OS_OSX
    _seeking=((BNMediaSlider *)_position).tracking;if(!_seeking){[self seekCommit];return;}
#endif
    NSString *text=BNMediaTime((int64_t)llround([self positionValue]));
#if TARGET_OS_OSX
    ((NSTextField *)_elapsed).stringValue=text;
#else
    ((UILabel *)_elapsed).text=text;
#endif
}
-(void)changeVolume:(id)sender{
#if TARGET_OS_OSX
    _settingVolume=((BNMediaSlider *)_volume).tracking;if(!_settingVolume)[self volumeCommit];
#endif
}
-(void)seekCommit{_seeking=NO;BNMediaCommand(_playerID,@"seek",@[@((int64_t)llround([self positionValue]))]);}
-(void)volumeCommit{_settingVolume=NO;BNMediaCommand(_playerID,@"set_volume",@[@(MIN(1,MAX(0,[self volumeValue])))]);}
-(void)update {
    NSDictionary *s=[BNMediaRuntime shared].states[_playerID];NSUInteger phase=s?[s[@"phase"] unsignedIntegerValue]:8;
    BOOL playable=s&&!BNIsNull(s[@"source"])&&phase!=0&&phase!=7&&phase!=8,playing=phase==3||phase==5,controllable=s&&phase!=8,seekable=playable&&[s[@"seekable"] boolValue]&&!BNIsNull(s[@"duration"]),muted=[s[@"muted"] boolValue];
    NSString *play=BNMediaText(playing?@"bern.media.pause":@"bern.media.play"),*mute=BNMediaText(muted?@"bern.media.unmute":@"bern.media.mute");
    NSString *elapsed=BNMediaTime([s[@"position"] longLongValue]),*duration=BNIsNull(s[@"duration"])?playable?BNMediaText(@"bern.media.live"):@"--:--":BNMediaTime([s[@"duration"] longLongValue]);
    double maximum=MAX(1,BNIsNull(s[@"duration"])?0:[s[@"duration"] doubleValue]);
#if TARGET_OS_OSX
    NSButton *playButton=(NSButton *)_playButton,*muteButton=(NSButton *)_muteButton;playButton.image=[NSImage imageWithSystemSymbolName:playing?@"pause.fill":@"play.fill" accessibilityDescription:play];muteButton.image=[NSImage imageWithSystemSymbolName:muted?@"speaker.slash.fill":@"speaker.wave.2.fill" accessibilityDescription:mute];playButton.toolTip=play;muteButton.toolTip=mute;playButton.enabled=playable;muteButton.enabled=controllable;
    NSSlider *position=(NSSlider *)_position,*volume=(NSSlider *)_volume;position.enabled=seekable;volume.enabled=controllable;position.maxValue=maximum;if(!_seeking)position.doubleValue=MIN(maximum,[s[@"position"] doubleValue]);if(!_settingVolume)volume.doubleValue=s?[s[@"volume"] doubleValue]:1;
    if(!_seeking)((NSTextField *)_elapsed).stringValue=elapsed;((NSTextField *)_duration).stringValue=duration;
#else
    UIButton *playButton=(UIButton *)_playButton,*muteButton=(UIButton *)_muteButton;[playButton setImage:[UIImage systemImageNamed:playing?@"pause.fill":@"play.fill"] forState:UIControlStateNormal];[muteButton setImage:[UIImage systemImageNamed:muted?@"speaker.slash.fill":@"speaker.wave.2.fill"] forState:UIControlStateNormal];playButton.enabled=playable;muteButton.enabled=controllable;
    UISlider *position=(UISlider *)_position,*volume=(UISlider *)_volume;position.enabled=seekable;volume.enabled=controllable;position.maximumValue=(float)maximum;if(!_seeking)position.value=(float)MIN(maximum,[s[@"position"] doubleValue]);if(!_settingVolume)volume.value=s?[s[@"volume"] floatValue]:1;
    if(!_seeking)((UILabel *)_elapsed).text=elapsed;((UILabel *)_duration).text=duration;
#endif
    _playButton.accessibilityLabel=play;_muteButton.accessibilityLabel=mute;_position.accessibilityLabel=BNMediaText(@"bern.media.position");_volume.accessibilityLabel=BNMediaText(@"bern.media.volume");
    if(_controls.count==4){_controls[0].enabled=playable;_controls[0].label=play;_controls[1].enabled=seekable;_controls[1].label=BNMediaText(@"bern.media.position");_controls[2].enabled=controllable;_controls[2].label=BNMediaText(@"bern.media.mute");_controls[3].enabled=controllable;_controls[3].label=BNMediaText(@"bern.media.volume");}
}
@end

static void BNMediaState(NSData *data) {
    BNMediaRuntime *runtime=[BNMediaRuntime shared];if(!runtime.handle)return;
    @try {BNReader *reader=[[BNReader alloc]initWithData:data];uint64_t revision=[reader u64];if(revision<runtime.revision)return;uint32_t count=[reader u32];NSMutableDictionary *states=[NSMutableDictionary dictionary];
        for(uint32_t i=0;i<count;i++){NSString *identifier=[reader text];NSString *owner=[reader text];BOOL bound=[reader u8]!=0;id source=[reader u8]?[reader text]:BNNull();int64_t version=(int64_t)[reader u64];uint32_t phase=[reader u32];if(phase>8)BNThrow(@"invalid_media_state",@"Unknown media phase");int64_t position=(int64_t)[reader u64];id duration=[reader u8]?@((int64_t)[reader u64]):BNNull();BOOL seekable=[reader u8]!=0;double volume=[reader f64];BOOL muted=[reader u8]!=0;id error=[reader u8]?[reader text]:BNNull();int64_t views=(int64_t)[reader u64];if([reader u8]){(void)[reader text];(void)[reader u32];(void)[reader u64];if([reader u8])(void)[reader text];}states[identifier]=@{@"owner":owner,@"bound":@(bound),@"source":source,@"version":@(version),@"phase":@(phase),@"position":@(position),@"duration":duration,@"seekable":@(seekable),@"volume":@(volume),@"muted":@(muted),@"error":error,@"views":@(views)};}
        if(reader.position!=data.length)BNThrow(@"invalid_media_state",@"Media state contains trailing bytes");runtime.revision=revision;runtime.states=states;
        // Media facts update the persistent media controls directly. Rebuilding
        // unrelated editors every 500 ms would interrupt the user's input.
        for(BNMediaSurface *surface in runtime.surfaces.allValues)if(surface.visible)[surface update];for(BNMediaControlsView *bar in runtime.bars.allValues)[bar update];
    }@catch(NSException *exception){[[BNHost shared]showError:exception.reason];}
}
static void BNMediaRequest(NSData *data) {
    BNMediaRuntime *runtime=[BNMediaRuntime shared];if(!runtime.handle)return;uint64_t request=0;
    @try {BNReader *reader=[[BNReader alloc]initWithData:data];request=[reader u64];NSString *identifier=[reader text];uint64_t version=[reader u64];uint32_t operation=[reader u32];
        if(operation==7){BNMediaAVPlayer *player=runtime.executors[identifier];[player stop];[runtime.executors removeObjectForKey:identifier];}
        else {BNMediaAVPlayer *player=[runtime player:identifier];
            if(operation==0){NSString *text=[reader text];NSURL *url=[text hasPrefix:@"/"]?[NSURL fileURLWithPath:text]:[NSURL URLWithString:text];if(!url.scheme.length)BNThrow(@"invalid_source",@"The source is not a media URL");[player load:url version:version];}
            else if(operation==1)[player unload:version];
            else {if(player.version!=version)BNThrow(@"stale_source",@"A newer source is loaded");
                if(operation==2){if(player.ended){player.ended=NO;[player.player seekToTime:kCMTimeZero];}player.started=YES;[player.player play];}
                else if(operation==3)[player.player pause];
                else if(operation==4){int64_t position=(int64_t)[reader u64];player.ended=NO;__weak BNMediaAVPlayer *weak=player;[player.player seekToTime:CMTimeMake(position,1000) toleranceBefore:kCMTimeZero toleranceAfter:kCMTimeZero completionHandler:^(BOOL finished){dispatch_async(dispatch_get_main_queue(), ^{[weak report];[[BNMediaRuntime shared]complete:request code:nil message:nil];});}];return;}
                else if(operation==5)player.player.volume=(float)[reader f64];
                else if(operation==6)player.player.muted=[reader u8]!=0;
                else BNThrow(@"unknown_command",@"Unknown media executor operation");
            }
        }
        if(reader.position!=data.length)BNThrow(@"invalid_request",@"Media request contains trailing bytes");[runtime complete:request code:nil message:nil];
    }@catch(NSException *exception){[runtime complete:request code:exception.name?:@"invalid_request" message:exception.reason];}
}
static void BNMediaStart(BernApp *app) {
    BNMediaRuntime *runtime=[BNMediaRuntime shared];runtime.handle=app;runtime.revision=0;
    BNWriter *offer=[BNWriter new];[offer u32:1];[offer u32:0];BNReader *answer=[[BNReader alloc]initWithData:BNTake(bern_media_kernel_attach(app,offer.data.bytes,offer.data.length))];
    runtime.kernel=[answer u8]!=0;if(runtime.kernel){if([answer u32]!=0)BNThrow(@"unsupported_surface",@"The media kernel selected an unsupported surface");}
    else {BNWriter *writer=[BNWriter new];[writer text:@"avfoundation"];[writer text:@"1"];[writer u8:1];[writer u8:1];BNTake(bern_media_executor_attached(app,writer.data.bytes,writer.data.length));}
    BNMediaState(BNTake(bern_media_snapshot(app)));
}
static BOOL BNMediaBind(NSString *player, NSString *owner, NSString *url) {
    BNMediaRuntime *runtime=[BNMediaRuntime shared];if(!runtime.handle)return NO;
    if(!runtime.owners[player]){BNWriter *writer=[BNWriter new];[writer text:player];[writer text:owner];BNReader *result=[[BNReader alloc]initWithData:BNTake(bern_media_create(runtime.handle,writer.data.bytes,writer.data.length))];if([result u8]){NSString *code=[result text];[[BNHost shared]showError:[NSString stringWithFormat:@"%@: %@",code,[result text]]];return NO;}runtime.owners[player]=owner;}
    BNWriter *writer=[BNWriter new];[writer text:player];[writer u8:url?1:0];if(url)[writer text:url];BNReader *result=[[BNReader alloc]initWithData:BNTake(bern_media_bind(runtime.handle,writer.data.bytes,writer.data.length))];if([result u8]){NSString *code=[result text];[[BNHost shared]showError:[NSString stringWithFormat:@"%@: %@",code,[result text]]];return NO;}return YES;
}
static BNView *BNMediaVideo(NSString *player, NSString *token, NSString *owner, NSString *fit, CGFloat corner) {
    BNMediaRuntime *runtime=[BNMediaRuntime shared];BNMediaSurface *surface=runtime.surfaces[token];
    if(surface&&![surface.playerID isEqual:player]){[surface detach];[runtime.surfaces removeObjectForKey:token];surface=nil;}
    if(!surface){surface=[[BNMediaSurface alloc]initWithFrame:CGRectMake(0,0,320,180)];surface.playerID=player;surface.token=token;surface.owner=owner;runtime.surfaces[token]=surface;}
    uint32_t mode=[fit isEqual:@"cover"]?1:[fit isEqual:@"fill"]?2:0;if(runtime.kernel&&surface.attached&&surface.fit!=mode)[surface detach];surface.visible=YES;[runtime.seenSurfaces addObject:token];surface.fit=mode;surface.corner=corner;[surface update];return surface;
}
// Descriptor expansion is also used by the renderer, preserving exactly the
// same conditions, component arguments and keyed iteration identities here.
static NSArray<NSDictionary *> *BNDescriptors(BNHost *, NSArray *, NSDictionary *);
static BOOL BNSearchContentsMounted(BNHost *, NSDictionary *, NSDictionary *);
static void BNMediaDeclarations(BNHost *host, NSArray *nodes, NSDictionary *locals, NSMutableSet *tokens, NSMutableSet *queries, NSUInteger depth) {
    if(depth>128)BNThrow(@"invalid_node",@"Media declaration expansion exceeds 128 levels");
    BNMediaRuntime *runtime=[BNMediaRuntime shared];BNWindow *window=locals[@"__window"];
    for(NSDictionary *descriptor in BNDescriptors(host,nodes,locals)) {
        NSDictionary *element=descriptor[@"element"],*scope=descriptor[@"locals"];NSString *kind=element[@"kind"];
        if([kind isEqual:@"Video"]) {
            NSString *name=BNString(element[@"id"]);if(!name.length)name=BNString(element[@"path"]);
            NSString *target=[NSString stringWithFormat:@"%@.%@%@",scope[@"__component"]?:@"",name,scope[@"__keys"]?:@""];
            [tokens addObject:[NSString stringWithFormat:@"%@/%@",window.identifier,target]];continue;
        }
        if([kind isEqual:@"Query"]) {
            NSString *key=[NSString stringWithFormat:@"%@#%llu:%@:%@%@",window.identifier,(unsigned long long)window.generation,scope[@"__component"]?:@"",element[@"path"],scope[@"__keys"]?:@""];[queries addObject:key];
            BNQuery *query=host.nativeQueries[key];if(query){query.locals=scope;query.binding=element[@"props"][@"query"][@"query"];}if(query.data)runtime.queryValues[key]=query.data;else if(query&&(query.phase==2||query.phase==4))runtime.queryValues[key]=BNNull();
            id data=runtime.queryValues[key];if(!BNIsNull(data)){NSMutableDictionary *inner=[scope mutableCopy];NSString *variable=element[@"template"][@"var"];if(variable)inner[variable]=data;BNMediaDeclarations(host,element[@"children"],inner,tokens,queries,depth+1);}continue;
        }
        if([kind isEqual:@"Navigation"]) {
            NSDictionary *field=element[@"props"][@"path"][@"field"];NSArray *path=field?BNArray([host field:field locals:scope]):@[];
            for(NSDictionary *child in BNArray(element[@"children"])) {
                if([child[@"kind"] isEqual:@"Destination"]) {
                    for(id route in path){NSMutableDictionary *inner=[scope mutableCopy];NSString *variable=child[@"template"][@"var"];if(variable)inner[variable]=route;BNMediaDeclarations(host,child[@"children"],inner,tokens,queries,depth+1);}
                } else BNMediaDeclarations(host,@[child],scope,tokens,queries,depth+1);
            }continue;
        }
        if([kind isEqual:@"Adaptive"]) {
            CGFloat width=window.root.bounds.size.width;if(width<=0)width=MAX(800,[window.definition[@"width"] doubleValue]);NSDictionary *points=BNDict(host.model[@"layouts"]);CGFloat compact=points.count?[points[@"compact_below"] doubleValue]:600;
            NSString *size=width<compact?@"compact":!BNIsNull(points[@"medium_below"])&&width<[points[@"medium_below"] doubleValue]?@"medium":!BNIsNull(points[@"expanded_below"])&&width>=[points[@"expanded_below"] doubleValue]?@"large":@"expanded";
            NSArray *order=@[@"compact",@"medium",@"expanded",@"large"];NSUInteger wanted=[order indexOfObject:size],distance=NSUIntegerMax;NSDictionary *chosen=nil;
            for(NSDictionary *child in BNArray(element[@"children"])){NSUInteger at=[order indexOfObject:BNString([host prop:child name:@"size" locals:scope])];if(at==NSNotFound)continue;NSUInteger d=at>=wanted?at-wanted:10+wanted-at;if(d<distance){distance=d;chosen=child;}}
            BNMediaDeclarations(host,chosen[@"children"],scope,tokens,queries,depth+1);continue;
        }
        if([kind isEqual:@"List"]&&!BNIsNull(element[@"props"][@"items"])) {NSMutableDictionary *each=[element mutableCopy];each[@"kind"]=@"ForEach";BNMediaDeclarations(host,@[each],scope,tokens,queries,depth+1);continue;}
        // Popover contents have their own mounting lifetime. A currently open
        // popover is retained by its live window below, rather than the button.
        if([kind isEqual:@"PopoverButton"]||[kind isEqual:@"SplitButton"])continue;
        if([kind isEqual:@"Search"]&&!BNSearchContentsMounted(host,element,scope))continue;
        if([kind isEqual:@"Inspector"]){id presented=[host prop:element name:@"presented" locals:scope];if(BNIsNull(presented)||![presented boolValue])continue;}
        // An inactive tab or a covered navigation root still owns its declared
        // source player. Only actual structural removal ends that ownership.
        BNMediaDeclarations(host,element[@"children"],scope,tokens,queries,depth+1);
    }
}
static NSSet<NSString *> *BNMediaLogicalQueryKeys(void) {
    BNMediaRuntime *runtime=[BNMediaRuntime shared];if(!runtime.logicalQueries){BNHost *host=[BNHost shared];NSMutableSet *tokens=[NSMutableSet set],*queries=[NSMutableSet set];for(BNWindow *window in host.windows.allValues)BNMediaDeclarations(host,@[window.definition[@"content"]],@{@"__window":window,@"__component":window.definition[@"id"],@"__keys":@""},tokens,queries,0);runtime.logicalTokens=tokens;runtime.logicalQueries=queries;}return runtime.logicalQueries;
}
static void BNMediaBeginRender(void) { BNMediaRuntime *runtime=[BNMediaRuntime shared];[runtime.seenSurfaces removeAllObjects];runtime.logicalTokens=nil;runtime.logicalQueries=nil; }
static void BNMediaEndRender(void) {
    BNMediaRuntime *runtime=[BNMediaRuntime shared];NSSet *queries=BNMediaLogicalQueryKeys(),*declarations=runtime.logicalTokens;
    for(NSString *key in [runtime.queryValues.allKeys copy])if(![queries containsObject:key])[runtime.queryValues removeObjectForKey:key];
    for(NSString *token in [runtime.surfaces.allKeys copy]) {
        BNMediaSurface *surface=runtime.surfaces[token];BOOL mounted=[runtime.seenSurfaces containsObject:token]||surface.window!=nil;
        if(!mounted){surface.visible=NO;[surface detach];if(![declarations containsObject:token])[runtime.surfaces removeObjectForKey:token];}
    }
    for(NSString *key in [runtime.bars.allKeys copy])if(![declarations containsObject:key]&&!runtime.bars[key].window)[runtime.bars removeObjectForKey:key];
    for(NSString *player in [runtime.owners.allKeys copy])if(![declarations containsObject:player]){
        BOOL mounted=NO;for(BNMediaSurface *surface in runtime.surfaces.allValues)if([surface.playerID isEqual:player]&&surface.window){mounted=YES;break;}
        if(!mounted){if(runtime.handle){BNWriter *writer=[BNWriter new];[writer text:player];bern_media_release(runtime.handle,writer.data.bytes,writer.data.length);}[runtime.owners removeObjectForKey:player];}
    }
}
static BNView *BNMediaControls(NSString *player, NSString *target, NSDictionary *locals) {
    BNMediaRuntime *runtime=[BNMediaRuntime shared];BNWindow *window=locals[@"__window"];NSString *key=[NSString stringWithFormat:@"%@/%@",window.identifier,target];BNMediaControlsView *bar=runtime.bars[key];
    if(!bar){bar=[[BNMediaControlsView alloc]initWithFrame:CGRectMake(0,0,440,30)];bar.owner=window.identifier;runtime.bars[key]=bar;}bar.playerID=player;
    NSMutableArray<BNControl *> *controls=[NSMutableArray array];NSArray *suffixes=@[@"play_pause",@"position",@"mute",@"volume"],*roles=@[@"button",@"slider",@"switch",@"slider"],*views=@[bar.playButton,bar.position,bar.muteButton,bar.volume];
    for(NSUInteger i=0;i<4;i++){NSString *identifier=[NSString stringWithFormat:@"%@.%@",target,suffixes[i]];BNControl *control=[[BNHost shared]registerControl:@{@"id":identifier,@"path":identifier,@"props":@{}} view:views[i] role:roles[i] label:@"" locals:locals];control.target=identifier;((BNView *)views[i]).accessibilityIdentifier=identifier;[controls addObject:control];}
    __weak BNMediaControlsView *weak=bar;controls[0].activate=^{[weak play];};controls[1].setNumber=^(double value){BNMediaControlsView *strong=weak;if(strong)BNMediaCommand(strong.playerID,@"seek",@[@((int64_t)llround(value))]);};controls[1].value=^{BNMediaControlsView *strong=weak;return BNNumberText([[BNMediaRuntime shared].states[strong.playerID][@"position"] doubleValue]);};controls[2].activate=^{[weak mute];};controls[2].setBool=^(BOOL value){BNMediaControlsView *strong=weak;if(strong)BNMediaCommand(strong.playerID,@"set_muted",@[@(value)]);};controls[2].value=^{BNMediaControlsView *strong=weak;return [[BNMediaRuntime shared].states[strong.playerID][@"muted"] boolValue]?@"true":@"false";};controls[3].setNumber=^(double value){BNMediaControlsView *strong=weak;if(strong)BNMediaCommand(strong.playerID,@"set_volume",@[@(MIN(1,MAX(0,value)))]);};controls[3].value=^{BNMediaControlsView *strong=weak;return BNNumberText([[BNMediaRuntime shared].states[strong.playerID][@"volume"] doubleValue]);};bar.controls=controls;[bar update];return bar;
}
static void BNMediaWindowClosed(NSString *owner) {
    BNMediaRuntime *runtime=[BNMediaRuntime shared];for(NSString *token in [runtime.surfaces.allKeys copy]){BNMediaSurface *surface=runtime.surfaces[token];if([surface.owner isEqual:owner]){[surface detach];[runtime.surfaces removeObjectForKey:token];}}
    for(NSString *key in [runtime.bars.allKeys copy])if([runtime.bars[key].owner isEqual:owner])[runtime.bars removeObjectForKey:key];
    for(NSString *player in [runtime.owners.allKeys copy])if([runtime.owners[player] isEqual:owner]){if(runtime.handle){BNWriter *writer=[BNWriter new];[writer text:player];bern_media_release(runtime.handle,writer.data.bytes,writer.data.length);}[runtime.owners removeObjectForKey:player];}
}
static void BNMediaStop(void) {
    BNMediaRuntime *runtime=[BNMediaRuntime shared];for(BNMediaSurface *surface in runtime.surfaces.allValues)[surface detach];[runtime.surfaces removeAllObjects];[runtime.bars removeAllObjects];[runtime.owners removeAllObjects];[runtime.queryValues removeAllObjects];for(BNMediaAVPlayer *player in runtime.executors.allValues)[player stop];[runtime.executors removeAllObjects];if(runtime.handle)bern_media_executor_detached(runtime.handle);[runtime.frameLock lock];runtime.handle=NULL;[runtime.frameLock unlock];runtime.states=@{};
}
