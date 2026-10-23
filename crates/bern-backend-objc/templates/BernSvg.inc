// The shared Bern SVG document is isolated from the application command bridge.
// Only Svg content uses WebKit; all application UI remains AppKit/UIKit.
#import <WebKit/WebKit.h>
static NSString * const BNSvgPrefix = @/*bern:svg-prefix*/;
static NSString * const BNSvgSuffix = @/*bern:svg-suffix*/;

@interface BNSvgView : WKWebView <WKNavigationDelegate>
@property(nonatomic,strong) NSString *sourceName;
@property(nonatomic,strong) NSDictionary *documentState;
@property(nonatomic,strong) NSData *lastApplied;
@property(nonatomic) BOOL documentLoaded;
@property(nonatomic) BOOL loadingInitialDocument;
-(void)applyDocumentState;
@end

@implementation BNSvgView
-(instancetype)init {
    WKWebViewConfiguration *configuration=[WKWebViewConfiguration new];
    configuration.websiteDataStore=[WKWebsiteDataStore nonPersistentDataStore];
    configuration.preferences.javaScriptCanOpenWindowsAutomatically=NO;
    if((self=[super initWithFrame:CGRectZero configuration:configuration])) {
        self.navigationDelegate=self;
#if TARGET_OS_OSX
        [self setValue:@NO forKey:@"drawsBackground"];
        [[NSNotificationCenter defaultCenter] addObserver:self selector:@selector(visibilityChanged:) name:NSApplicationDidBecomeActiveNotification object:nil];
        [[NSNotificationCenter defaultCenter] addObserver:self selector:@selector(visibilityChanged:) name:NSApplicationDidResignActiveNotification object:nil];
#else
        self.opaque=NO; self.backgroundColor=UIColor.clearColor;
        self.scrollView.backgroundColor=UIColor.clearColor; self.scrollView.scrollEnabled=NO;
        self.accessibilityElementsHidden=YES;
        [[NSNotificationCenter defaultCenter] addObserver:self selector:@selector(visibilityChanged:) name:UIApplicationDidBecomeActiveNotification object:nil];
        [[NSNotificationCenter defaultCenter] addObserver:self selector:@selector(visibilityChanged:) name:UIApplicationWillResignActiveNotification object:nil];
#endif
    }
    return self;
}
-(void)dealloc { [[NSNotificationCenter defaultCenter] removeObserver:self]; self.navigationDelegate=nil; [self stopLoading]; }
-(void)visibilityChanged:(NSNotification *)notification { [self applyDocumentState]; }
#if TARGET_OS_OSX
-(void)viewDidMoveToWindow { [super viewDidMoveToWindow]; [self applyDocumentState]; }
-(void)viewDidChangeEffectiveAppearance { [super viewDidChangeEffectiveAppearance]; [self applyDocumentState]; }
-(NSArray *)accessibilityChildren { return @[]; }
#else
-(void)didMoveToWindow { [super didMoveToWindow]; [self applyDocumentState]; }
-(void)traitCollectionDidChange:(UITraitCollection *)previousTraitCollection { [super traitCollectionDidChange:previousTraitCollection]; [self applyDocumentState]; }
#endif
-(void)setHidden:(BOOL)hidden { [super setHidden:hidden]; [self applyDocumentState]; }
-(void)applyDocumentState {
    if(!_documentLoaded || !_documentState) return;
    NSMutableDictionary *state=[_documentState mutableCopy];
    BOOL visible=self.window!=nil && !self.hidden;
    for(BNView *parent=self.superview;parent;parent=parent.superview) if(parent.hidden) { visible=NO; break; }
#if TARGET_OS_OSX
    state[@"scheme"]=BNDark(self)?@"dark":@"light";
    visible=visible && NSApp.active;
#else
    state[@"scheme"]=self.traitCollection.userInterfaceStyle==UIUserInterfaceStyleDark?@"dark":@"light";
    visible=visible && [UIApplication sharedApplication].applicationState==UIApplicationStateActive;
#endif
    state[@"visible"]=@(visible);
    NSData *data=[NSJSONSerialization dataWithJSONObject:state options:NSJSONWritingSortedKeys error:nil];
    if(!data || [data isEqual:_lastApplied]) return;
    _lastApplied=data;
    NSString *json=[[NSString alloc] initWithData:data encoding:NSUTF8StringEncoding];
    [self evaluateJavaScript:[NSString stringWithFormat:@"window.bernSvg?.update(%@)",json] completionHandler:nil];
}
-(void)webView:(WKWebView *)webView didFinishNavigation:(WKNavigation *)navigation {
    _documentLoaded=YES; _loadingInitialDocument=NO; [self applyDocumentState];
}
-(void)webView:(WKWebView *)webView decidePolicyForNavigationAction:(WKNavigationAction *)action decisionHandler:(void (^)(WKNavigationActionPolicy))decisionHandler {
    BOOL initial=_loadingInitialDocument && [action.request.URL.absoluteString isEqual:@"about:blank"];
    decisionHandler(initial?WKNavigationActionPolicyAllow:WKNavigationActionPolicyCancel);
}
-(void)webView:(WKWebView *)webView didFailNavigation:(WKNavigation *)navigation withError:(NSError *)error { NSLog(@"Bern SVG %@: %@",_sourceName,error.localizedDescription); }
-(void)webView:(WKWebView *)webView didFailProvisionalNavigation:(WKNavigation *)navigation withError:(NSError *)error { NSLog(@"Bern SVG %@: %@",_sourceName,error.localizedDescription); }
@end

@interface BNSvgContainer : BNView
@property(nonatomic,strong) BNSvgView *document;
@end
@implementation BNSvgContainer
#if TARGET_OS_OSX
-(BOOL)isFlipped { return YES; }
-(void)layout { [super layout]; _document.frame=self.bounds; }
-(NSArray *)accessibilityChildren { return @[]; }
#else
-(void)layoutSubviews { [super layoutSubviews]; _document.frame=self.bounds; }
#endif
@end

static BNView *BNRenderSvg(BNHost *host, NSDictionary *element, NSDictionary *locals) {
    BNWindow *window=locals[@"__window"];
    NSMapTable *cache=objc_getAssociatedObject(window,@selector(applyDocumentState));
    if(!cache) { cache=[NSMapTable strongToWeakObjectsMapTable]; objc_setAssociatedObject(window,@selector(applyDocumentState),cache,OBJC_ASSOCIATION_RETAIN_NONATOMIC); }
    NSString *key=[NSString stringWithFormat:@"%@.%@%@",locals[@"__component"]?:@"",element[@"path"],locals[@"__keys"]?:@""];
    BNSvgContainer *container=[cache objectForKey:key];
    if(!container) { container=[BNSvgContainer new]; container.document=[BNSvgView new]; [container addSubview:container.document]; [cache setObject:container forKey:key]; }
    BNSvgView *view=container.document;
    NSString *source=BNPropString(host,element,@"source",locals), *label=BNPropString(host,element,@"label",locals);
    double speed=BNPropNumber(host,element,@"speed",locals,1),restart=BNPropNumber(host,element,@"restart",locals,0);
    view.documentState=@{@"playing":@(BNPropBool(host,element,@"playing",locals,YES)),@"interactive":@(BNPropBool(host,element,@"interactive",locals,YES)),@"fit":BNPropString(host,element,@"fit",locals).length?BNPropString(host,element,@"fit",locals):@"contain",@"speed":@(isfinite(speed)&&speed>0?speed:1),@"restart":@(isfinite(restart)?restart:0)};
#if TARGET_OS_OSX
    [container setAccessibilityElement:label.length>0]; [container setAccessibilityLabel:label]; [view setAccessibilityElement:NO];
#else
    container.isAccessibilityElement=label.length>0; container.accessibilityLabel=label; container.accessibilityTraits=UIAccessibilityTraitImage;
#endif
    if(![view.sourceName isEqual:source]) {
        view.sourceName=source; view.documentLoaded=NO; view.lastApplied=nil;
        NSURL *url=[[NSBundle mainBundle].resourceURL URLByAppendingPathComponent:source];
        NSError *error=nil; NSString *svg=[NSString stringWithContentsOfURL:url encoding:NSUTF8StringEncoding error:&error];
        if(!svg) BNThrow(@"resource_unavailable",[NSString stringWithFormat:@"SVG %@: %@",source,error.localizedDescription]);
        view.loadingInitialDocument=YES;
        [view loadHTMLString:[NSString stringWithFormat:@"%@%@%@",BNSvgPrefix,svg,BNSvgSuffix] baseURL:nil];
    } else [view applyDocumentState];
    return container;
}
