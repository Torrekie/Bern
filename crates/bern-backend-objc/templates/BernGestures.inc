// Included after BernRenderer.inc: the same layout and descriptor helpers are
// used for gesture content and every ordinary container.
static NSMapTable<NSString *,BNView *> *BNGestureViews(void) {
    static NSMapTable *views;static dispatch_once_t once;dispatch_once(&once,^{views=[NSMapTable strongToWeakObjectsMapTable];});
    for(NSString *key in views.keyEnumerator.allObjects)if(![views objectForKey:key])[views removeObjectForKey:key];return views;
}
static NSString *BNGestureIdentity(BNHost *host, NSDictionary *element, NSDictionary *locals) {
    BNWindow *window=locals[@"__window"];return [NSString stringWithFormat:@"%@#%llu:%@:%@%@",window.identifier,(unsigned long long)window.generation,locals[@"__component"]?:@"",element[@"path"],locals[@"__keys"]?:@""];
}
static BOOL BNMotionReduced(BNView *,BNHost *);
@class BNGestureView;
#if TARGET_OS_OSX
@interface BNGestureTarget:NSObject<NSGestureRecognizerDelegate>
#else
@interface BNGestureTarget:NSObject<UIGestureRecognizerDelegate>
#endif
@property(nonatomic,weak)BNGestureView *view;
-(void)changed:(id)recognizer;
@end
@interface BNGestureView:BNLayout
@property(nonatomic,weak)BNHost *host;
@property(nonatomic,strong)NSDictionary *element;
@property(nonatomic,strong)NSDictionary *locals;
@property(nonatomic,strong)BNGestureTarget *coordinator;
@property(nonatomic)BOOL pinch;
@property(nonatomic)BOOL horizontal;
@property(nonatomic)BOOL interacting;
@property(nonatomic)BOOL changed;
@property(nonatomic)double startValue;
@property(nonatomic)double minimum;
@property(nonatomic)double maximum;
@property(nonatomic)double distance;
-(void)recognize:(id)recognizer;
-(void)rebuild;
-(void)apply:(double)value commit:(BOOL)commit;
@end
@implementation BNGestureTarget
-(void)changed:(id)recognizer{[_view recognize:recognizer];}
#if TARGET_OS_OSX
-(BOOL)gestureRecognizer:(NSGestureRecognizer *)recognizer shouldRecognizeSimultaneouslyWithGestureRecognizer:(NSGestureRecognizer *)other{return _view.pinch;}
#else
-(BOOL)gestureRecognizer:(UIGestureRecognizer *)recognizer shouldRecognizeSimultaneouslyWithGestureRecognizer:(UIGestureRecognizer *)other{return _view.pinch;}
#endif
@end
@implementation BNGestureView
-(instancetype)initWithFrame:(CGRect)frame {
    if((self=[super initWithFrame:frame])){self.axis=@"column";self.gap=0;self.fillWidth=YES;_coordinator=[BNGestureTarget new];_coordinator.view=self;}return self;
}
-(void)rebuild {
    // A drag updates the draft continuously. Rebuild only the gesture's
    // content while the host defers moving its active native recognizer.
    NSMutableArray *controls=[NSMutableArray array];
    for(BNControl *control in _host.controls){BNView *view=control.view;BOOL inside=NO;for(BNView *parent=view.superview;parent;parent=parent.superview)if(parent==self){inside=YES;break;}if(!inside)[controls addObject:control];}
    _host.controls=controls;for(BNView *child in [self.subviews copy])[child removeFromSuperview];
    for(BNView *child in BNRendered(_host,_element[@"children"],_locals))[self addSubview:child];
    [self invalidateIntrinsicContentSize];[self arrange];
}
-(double)value{return [[_host field:_element[@"props"][@"value"][@"field"] locals:_locals] doubleValue];}
-(void)apply:(double)value commit:(BOOL)commit {
    value=MIN(_maximum,MAX(_minimum,value));NSDictionary *field=_element[@"props"][@"value"][@"field"];
    if([_host setField:field value:@(value) locals:_locals]){
#if TARGET_OS_OSX
        self.accessibilityValue=@(value);
#else
        self.accessibilityValue=BNNumberText(value);
#endif
        if(_interacting)[self rebuild];if(commit)[_host action:_element[@"action"] locals:_locals];
    }
}
-(void)recognize:(id)recognizer {
    @try {
#if TARGET_OS_OSX
        NSGestureRecognizerState state=((NSGestureRecognizer *)recognizer).state;BOOL began=state==NSGestureRecognizerStateBegan,ended=state==NSGestureRecognizerStateEnded,cancelled=state==NSGestureRecognizerStateCancelled||state==NSGestureRecognizerStateFailed;
#else
        UIGestureRecognizerState state=((UIGestureRecognizer *)recognizer).state;BOOL began=state==UIGestureRecognizerStateBegan,ended=state==UIGestureRecognizerStateEnded,cancelled=state==UIGestureRecognizerStateCancelled||state==UIGestureRecognizerStateFailed;
#endif
        if(began&&!_interacting){_startValue=[self value];_changed=NO;_interacting=YES;[_host beginInteraction];}
        if(!_interacting)return;
        if(!cancelled){double value=_startValue;
            if(_pinch){
#if TARGET_OS_OSX
                value*=1+((NSMagnificationGestureRecognizer *)recognizer).magnification;
#else
                value*=((UIPinchGestureRecognizer *)recognizer).scale;
#endif
                _changed=YES;
            }else{
#if TARGET_OS_OSX
                CGPoint translation=[(NSPanGestureRecognizer *)recognizer translationInView:self];
#else
                CGPoint translation=[(UIPanGestureRecognizer *)recognizer translationInView:self];
#endif
                if(hypot(translation.x,translation.y)>=10)_changed=YES;
                value+=(_horizontal?translation.x:-translation.y)/MAX(0.001,_distance)*(_maximum-_minimum);
            }
            if(_changed)[self apply:value commit:NO];
        }
        if(ended||cancelled){BOOL commit=ended&&_changed;_interacting=NO;@try{if(commit)[_host action:_element[@"action"] locals:_locals];}@finally{[_host endInteraction];}}
    }@catch(NSException *error){if(_interacting){_interacting=NO;[_host endInteraction];}[_host showError:error.reason];}
}
#if TARGET_OS_OSX
-(BOOL)accessibilityPerformIncrement{[self apply:[self value]+(_maximum-_minimum)/10 commit:YES];return YES;}
-(BOOL)accessibilityPerformDecrement{[self apply:[self value]-(_maximum-_minimum)/10 commit:YES];return YES;}
-(id)accessibilityMinValue{return @(_minimum);}
-(id)accessibilityMaxValue{return @(_maximum);}
#else
-(void)accessibilityIncrement{[self apply:[self value]+(_maximum-_minimum)/10 commit:YES];}
-(void)accessibilityDecrement{[self apply:[self value]-(_maximum-_minimum)/10 commit:YES];}
#endif
-(void)dealloc{if(_interacting)[_host endInteraction];}
@end

static BNView *BNRenderGesture(BNHost *host,NSDictionary *element,NSDictionary *locals) {
    NSString *key=BNGestureIdentity(host,element,locals);BNGestureView *view=(BNGestureView *)[BNGestureViews() objectForKey:key];BOOL pinch=[element[@"kind"] isEqual:@"Pinch"];
    if(![view isKindOfClass:BNGestureView.class]) {
        view=[[BNGestureView alloc]initWithFrame:CGRectZero];view.pinch=pinch;
#if TARGET_OS_OSX
        NSGestureRecognizer *recognizer=pinch?[[NSMagnificationGestureRecognizer alloc]initWithTarget:view.coordinator action:@selector(changed:)]:[[NSPanGestureRecognizer alloc]initWithTarget:view.coordinator action:@selector(changed:)];recognizer.delegate=view.coordinator;[view addGestureRecognizer:recognizer];
#else
        UIGestureRecognizer *recognizer=pinch?[[UIPinchGestureRecognizer alloc]initWithTarget:view.coordinator action:@selector(changed:)]:[[UIPanGestureRecognizer alloc]initWithTarget:view.coordinator action:@selector(changed:)];recognizer.delegate=view.coordinator;recognizer.cancelsTouchesInView=!pinch;[view addGestureRecognizer:recognizer];
#endif
        [BNGestureViews() setObject:view forKey:key];
    }
    view.host=host;view.element=element;view.locals=locals;view.horizontal=[BNPropString(host,element,@"axis",locals) isEqual:@"horizontal"];view.minimum=BNPropNumber(host,element,@"min",locals,0);view.maximum=BNPropNumber(host,element,@"max",locals,1);view.distance=BNPropNumber(host,element,@"distance",locals,300);
    [view rebuild];NSString *label=BNPropString(host,element,@"label",locals);BNControl *control=[host registerControl:element view:view role:pinch?@"pinch":@"swipe" label:label locals:locals];__weak BNGestureView *weak=view;control.setNumber=^(double value){[weak apply:value commit:YES];};control.value=^{return BNNumberText([weak value]);};
#if TARGET_OS_OSX
    [view setAccessibilityElement:YES];view.accessibilityRole=NSAccessibilitySliderRole;view.accessibilityValue=@([view value]);
#else
    view.isAccessibilityElement=YES;view.accessibilityTraits|=UIAccessibilityTraitAdjustable;view.accessibilityValue=BNNumberText([view value]);
#endif
    return view;
}

@interface BNMarqueeView:BNView
@property(nonatomic,weak)BNHost *host;
@property(nonatomic,strong)NSDictionary *element;
@property(nonatomic,strong)NSDictionary *locals;
@property(nonatomic,strong)BNLayout *content;
@property(nonatomic)double start;
@property(nonatomic)double elapsed;
@property(nonatomic)BOOL paused;
@property(nonatomic)BOOL initialized;
@property(nonatomic)double duration;
@property(nonatomic)double phase;
-(void)arrange;
@end
@implementation BNMarqueeView
-(instancetype)initWithFrame:(CGRect)frame {
    if((self=[super initWithFrame:frame])){
#if TARGET_OS_OSX
        self.wantsLayer=YES;[[NSWorkspace sharedWorkspace].notificationCenter addObserver:self selector:@selector(motionChanged:) name:NSWorkspaceAccessibilityDisplayOptionsDidChangeNotification object:nil];
#else
        [[NSNotificationCenter defaultCenter]addObserver:self selector:@selector(motionChanged:) name:UIAccessibilityReduceMotionStatusDidChangeNotification object:nil];
#endif
        self.layer.masksToBounds=YES;_start=CACurrentMediaTime();
    }return self;
}
-(void)motionChanged:(NSNotification *)notification{if(NSThread.isMainThread)[self arrange];else{__weak BNMarqueeView *weak=self;dispatch_async(dispatch_get_main_queue(),^{[weak arrange];});}}
#if TARGET_OS_OSX
-(BOOL)isFlipped{return YES;}
-(void)layout{[super layout];[self arrange];}
#else
-(void)layoutSubviews{[super layoutSubviews];[self arrange];}
#endif
-(CGSize)intrinsicContentSize {CGSize content=[_content measure:CGSizeMake(100000,100000)];return CGSizeMake(content.width,content.height);}
-(void)arrange {
    if(!_content)return;CGSize size=[_content measure:CGSizeMake(100000,MAX(1,self.bounds.size.height))];BNPlace(_content,CGRectMake(0,0,size.width,MAX(size.height,self.bounds.size.height)));CALayer *layer=BNLayer(_content);
    double time=_elapsed+(_paused?0:CACurrentMediaTime()-_start),progress=fmod(_phase+time/MAX(1,_duration),1);
    BOOL reduced=BNMotionReduced(self,_host)||BNPropBool(_host,_element,@"reduce_motion",_locals,NO);double width=self.bounds.size.width,x=reduced?width*0.28:width-(width+size.width)*progress;
    [CATransaction begin];[CATransaction setDisableActions:YES];[layer removeAnimationForKey:@"bernMarquee"];[layer setValue:@(x) forKeyPath:@"transform.translation.x"];[CATransaction commit];
    if(!_paused&&!reduced&&width>0){CABasicAnimation *animation=[CABasicAnimation animationWithKeyPath:@"transform.translation.x"];animation.fromValue=@(width);animation.toValue=@(-size.width);animation.duration=MAX(1,_duration);animation.repeatCount=HUGE_VALF;animation.beginTime=[layer convertTime:CACurrentMediaTime() fromLayer:nil]-progress*animation.duration;animation.timingFunction=[CAMediaTimingFunction functionWithName:kCAMediaTimingFunctionLinear];[layer addAnimation:animation forKey:@"bernMarquee"];}
}
-(void)dealloc {
#if TARGET_OS_OSX
    [[NSWorkspace sharedWorkspace].notificationCenter removeObserver:self];
#else
    [[NSNotificationCenter defaultCenter]removeObserver:self];
#endif
}
@end
static BNView *BNRenderMarquee(BNHost *host,NSDictionary *element,NSDictionary *locals) {
    NSString *key=BNGestureIdentity(host,element,locals);BNMarqueeView *view=(BNMarqueeView *)[BNGestureViews() objectForKey:key];if(![view isKindOfClass:BNMarqueeView.class]){view=[[BNMarqueeView alloc]initWithFrame:CGRectZero];[BNGestureViews() setObject:view forKey:key];}
    BOOL paused=BNPropBool(host,element,@"paused",locals,NO);double now=CACurrentMediaTime();if(view.initialized&&paused!=view.paused){if(paused)view.elapsed+=now-view.start;else view.start=now;}view.initialized=YES;view.paused=paused;view.duration=MAX(1,BNPropNumber(host,element,@"duration",locals,1));view.phase=BNPropNumber(host,element,@"phase",locals,0);view.host=host;view.element=element;view.locals=locals;
    BNLayout *content=BNContainer(@"row",0);for(BNView *child in BNRendered(host,element[@"children"],locals))[content addSubview:child];CALayer *layer=BNLayer(content);layer.shadowColor=BNColor.blackColor.CGColor;layer.shadowOpacity=1;layer.shadowRadius=1;layer.shadowOffset=CGSizeMake(0,1);[view.content removeFromSuperview];view.content=content;[view addSubview:content];double opacity=MIN(1,MAX(0,BNPropNumber(host,element,@"opacity",locals,1)));
#if TARGET_OS_OSX
    view.alphaValue=opacity;
#else
    view.alpha=opacity;
#endif
    BNSetMeta(view,@{@"fillWidth":@YES});[view arrange];return view;
}
