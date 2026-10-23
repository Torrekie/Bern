// CoreAnimation motion for the shared Darwin 20 renderer. The host brackets a
// render with Begin/End, so geometry and transition ownership survive rebuilding
// the native tree. Snapshot layers are removed when their finite animation ends.
@interface BNMotionFrame : NSObject
@property(nonatomic,weak) BNView *view;
@property(nonatomic,weak) BNWindow *window;
@property(nonatomic,strong) NSDictionary *element;
@property(nonatomic,strong) NSDictionary *locals;
@property(nonatomic,strong) NSString *key;
@property(nonatomic,strong) NSString *hero;
@property(nonatomic,strong) id nudge;
@property(nonatomic) CGRect rect;
@property(nonatomic) CGRect relative;
@property(nonatomic) CGFloat opacity;
@property(nonatomic) BOOL reduce;
@property(nonatomic,strong) id image;
@end
@implementation BNMotionFrame
@end
@interface BNMotionState : NSObject
@property(nonatomic,strong) NSDictionary<NSString *,BNMotionFrame *> *previous;
@property(nonatomic,strong) NSMutableArray<CALayer *> *overlays;
@property(nonatomic) BOOL started;
@end
@implementation BNMotionState
-(instancetype)init {if((self=[super init])){_previous=@{};_overlays=[NSMutableArray array];}return self;}
@end
static NSValue *BNMotionPoint(CGPoint point) {
#if TARGET_OS_OSX
    return [NSValue valueWithPoint:point];
#else
    return [NSValue valueWithCGPoint:point];
#endif
}
static NSValue *BNMotionRect(CGRect rect) {
#if TARGET_OS_OSX
    return [NSValue valueWithRect:rect];
#else
    return [NSValue valueWithCGRect:rect];
#endif
}
static const void *BNMotionStateKey=&BNMotionStateKey;
static BNMotionState *BNMotionStore(BNHost *host) {BNMotionState *state=objc_getAssociatedObject(host,BNMotionStateKey);if(!state){state=[BNMotionState new];objc_setAssociatedObject(host,BNMotionStateKey,state,OBJC_ASSOCIATION_RETAIN_NONATOMIC);}return state;}
static BOOL BNMotionReduced(BNView *view, BNHost *host) {
#if TARGET_OS_OSX
    if(NSWorkspace.sharedWorkspace.accessibilityDisplayShouldReduceMotion)return YES;
#else
    if(UIAccessibilityIsReduceMotionEnabled())return YES;
#endif
    for(BNView *current=view;current;current=current.superview){NSDictionary *meta=BNMeta(current);if(BNPropBool(host,BNDict(meta[@"element"]),@"reduce_motion",BNDict(meta[@"locals"]),NO))return YES;}return NO;
}
static id BNMotionImage(BNView *view) {
    CGSize size=view.bounds.size;if(size.width<=0 || size.height<=0)return nil;
#if TARGET_OS_OSX
    CGFloat scale=view.window.backingScaleFactor ?: 1;
#else
    CGFloat scale=view.window.screen.scale ?: UIScreen.mainScreen.scale;
#endif
    CGFloat cap=MIN(1,2048.0/MAX(size.width*scale,size.height*scale));scale*=cap;NSUInteger width=MAX(1,(NSUInteger)ceil(size.width*scale)),height=MAX(1,(NSUInteger)ceil(size.height*scale));
    CGColorSpaceRef space=CGColorSpaceCreateDeviceRGB();CGContextRef context=CGBitmapContextCreate(NULL,width,height,8,0,space,kCGImageAlphaPremultipliedLast);CGColorSpaceRelease(space);if(!context)return nil;CGContextScaleCTM(context,scale,scale);[BNLayer(view) renderInContext:context];CGImageRef image=CGBitmapContextCreateImage(context);CGContextRelease(context);return CFBridgingRelease(image);
}
static NSString *BNMotionIdentity(BNView *view, BNWindow *window) {
    NSDictionary *meta=BNMeta(view),*element=BNDict(meta[@"element"]),*locals=BNDict(meta[@"locals"]);if(!element.count)return nil;
    return [NSString stringWithFormat:@"%@/%@/%@%@",window.identifier,locals[@"__component"] ?: @"",element[@"path"] ?: element[@"id"] ?: element[@"kind"],locals[@"__keys"] ?: @""];
}
static void BNMotionCollect(BNHost *host, BNWindow *window, BNView *view, NSMutableDictionary *frames, BOOL snapshots) {
    if(view.hidden)return;NSDictionary *meta=BNMeta(view),*element=BNDict(meta[@"element"]),*locals=BNDict(meta[@"locals"]);NSString *key=BNMotionIdentity(view,window);
    if(key){BNMotionFrame *frame=[BNMotionFrame new];frame.key=key;frame.view=view;frame.window=window;frame.element=element;frame.locals=locals;frame.rect=[view convertRect:view.bounds toView:window.root];frame.relative=view.frame;frame.opacity=BNLayer(view).opacity;frame.reduce=BNMotionReduced(view,host);
        NSString *hero=BNPropString(host,element,@"hero",locals);if(hero.length){id heroKey=[host prop:element name:@"hero_key" locals:locals];frame.hero=[NSString stringWithFormat:@"%@/%@/%@",window.identifier,hero,BNString(heroKey)];}
        id nudgeKey=[host prop:element name:@"nudge_key" locals:locals];frame.nudge=!BNIsNull(nudgeKey) ? nudgeKey : @(BNPropBool(host,element,@"nudge",locals,NO));
        if(snapshots && (frame.hero.length || BNPropString(host,element,@"disappear",locals).length))frame.image=BNMotionImage(view);
        frames[key]=frame;
    }
    for(BNView *child in view.subviews)BNMotionCollect(host,window,child,frames,snapshots);
}
static NSDictionary *BNMotionFrames(BNHost *host, BOOL snapshots) {NSMutableDictionary *frames=[NSMutableDictionary dictionary];for(BNWindow *window in host.windows.allValues)if(window.root.content)BNMotionCollect(host,window,window.root.content,frames,snapshots);return frames;}
static NSDictionary *BNMotionToken(BNHost *host, NSString *name) {for(NSDictionary *token in BNArray(BNDict(host.model[@"style"])[@"motion"]))if([token[@"name"] isEqual:name])return token;return @{@"period":@0.45,@"damping":@1};}
static CAPropertyAnimation *BNMotionAnimation(BNHost *host, NSString *path, id from, id to, NSString *token, BOOL reduced) {
    if(reduced){CABasicAnimation *animation=[CABasicAnimation animationWithKeyPath:path];animation.fromValue=from;animation.toValue=to;animation.duration=0.15;animation.timingFunction=[CAMediaTimingFunction functionWithName:kCAMediaTimingFunctionEaseInEaseOut];return animation;}
    NSDictionary *motion=BNMotionToken(host,token);CGFloat period=MAX(0.03,[motion[@"period"] doubleValue]),damping=MAX(0.01,[motion[@"damping"] doubleValue]);CASpringAnimation *animation=[CASpringAnimation animationWithKeyPath:path];animation.mass=1;animation.stiffness=pow(2*M_PI/period,2);animation.damping=4*M_PI*damping/period;animation.initialVelocity=0;animation.fromValue=from;animation.toValue=to;animation.duration=MAX(0.05,MIN(3,animation.settlingDuration));return animation;
}
static NSDictionary *BNMotionTransition(BNHost *host, NSString *name) {for(NSDictionary *transition in BNArray(BNDict(host.model[@"style"])[@"transitions"]))if([transition[@"name"] isEqual:name])return transition;return @{@"kind":@{@"kind":@"fade"},@"motion":@"smooth"};}
static void BNMotionTransitionOnLayer(BNHost *host, CALayer *layer, BNMotionFrame *frame, NSString *name, BOOL appearing, CGFloat delay, void (^completion)(void)) {
    NSDictionary *transition=BNMotionTransition(host,name),*kind=BNDict(transition[@"kind"]);NSString *type=BNString(kind[@"kind"]),*token=BNString(transition[@"motion"]);BOOL reduce=frame.reduce;NSMutableArray *animations=[NSMutableArray array];
    CGFloat alpha=frame.opacity;[animations addObject:BNMotionAnimation(host,@"opacity",@(appearing ? 0 : alpha),@(appearing ? alpha : 0),token,YES)];
    if(!reduce && ![type isEqual:@"fade"]){CATransform3D delta=CATransform3DIdentity;
        if([type isEqual:@"pop"]){CGFloat scale=kind[@"from"] ? [kind[@"from"] doubleValue] : 0.8;delta=CATransform3DMakeScale(scale,scale,1);}
        else {NSString *edge=BNString(kind[@"edge"]);BOOL horizontal=[@[@"leading",@"trailing"] containsObject:edge];CGFloat sign=([edge isEqual:@"leading"] || [edge isEqual:@"top"]) ? -1 : 1;
            if([type isEqual:@"grow"]){CGFloat x=horizontal ? 0.001 : 1,y=horizontal ? 1 : 0.001;delta=CATransform3DMakeScale(x,y,1);CGFloat shift=sign*(horizontal ? frame.rect.size.width : frame.rect.size.height)/2;delta=CATransform3DTranslate(delta,horizontal ? shift : 0,horizontal ? 0 : shift,0);}
            else {CGFloat distance=kind[@"distance"] ? [kind[@"distance"] doubleValue] : 16;delta=CATransform3DMakeTranslation(horizontal ? sign*distance : 0,horizontal ? 0 : sign*distance,0);}
        }
        CATransform3D normal=layer.transform,moved=CATransform3DConcat(normal,delta);[animations addObject:BNMotionAnimation(host,@"transform",[NSValue valueWithCATransform3D:appearing ? moved : normal],[NSValue valueWithCATransform3D:appearing ? normal : moved],token,NO)];
    }
    CAAnimationGroup *group=[CAAnimationGroup animation];group.animations=animations;CGFloat duration=0;for(CAAnimation *animation in animations)duration=MAX(duration,animation.duration);group.duration=duration;group.beginTime=CACurrentMediaTime()+MAX(0,delay);group.fillMode=kCAFillModeBoth;group.removedOnCompletion=YES;
    [CATransaction begin];if(completion)[CATransaction setCompletionBlock:completion];[layer addAnimation:group forKey:appearing ? @"bern.appear" : @"bern.disappear"];[CATransaction commit];
}
static CALayer *BNMotionOverlay(BNMotionState *state, BNMotionFrame *frame) {
    if(!frame.image || !frame.window)return nil;CALayer *overlay=[CALayer layer];overlay.contents=frame.image;overlay.contentsGravity=kCAGravityResize;overlay.frame=frame.rect;overlay.opacity=frame.opacity;[BNLayer(frame.window.root) addSublayer:overlay];[state.overlays addObject:overlay];return overlay;
}
static void BNMotionBegin(BNHost *host) {
    BNMotionState *state=BNMotionStore(host);NSDictionary *saved=state.previous;NSDictionary *captured=BNMotionFrames(host,YES);for(NSString *key in captured){BNMotionFrame *frame=captured[key],*old=saved[key];if(old){frame.nudge=old.nudge;frame.hero=old.hero;}}state.previous=captured;
    for(CALayer *layer in [state.overlays copy])[layer removeFromSuperlayer];[state.overlays removeAllObjects];
}
static void BNMotionInitializeReveal(BNView *view);
static void BNMotionRevealChildren(BNView *view);
static void BNMotionEnd(BNHost *host) {
    BNPopoverPrune(host,NO);BNMotionState *state=BNMotionStore(host);NSDictionary *now=BNMotionFrames(host,NO),*before=state.previous;NSMutableDictionary *oldHeroes=[NSMutableDictionary dictionary];for(BNMotionFrame *old in before.allValues)if(old.hero.length && old.image)oldHeroes[old.hero]=old;
    for(BNMotionFrame *frame in now.allValues){BNMotionFrame *old=before[frame.key];BNView *view=frame.view;if(!view)continue;CALayer *layer=BNLayer(view);NSString *reflow=BNPropString(host,frame.element,@"reflow",frame.locals),*animate=BNPropString(host,frame.element,@"animate",frame.locals);
        if(old && !frame.reduce){
            if(reflow.length || animate.length){CGFloat dx=old.relative.origin.x-frame.relative.origin.x,dy=old.relative.origin.y-frame.relative.origin.y;if(fabs(dx)>0.25 || fabs(dy)>0.25){CATransform3D normal=layer.transform,from=CATransform3DConcat(CATransform3DMakeTranslation(dx,dy,0),normal);[layer addAnimation:BNMotionAnimation(host,@"transform",[NSValue valueWithCATransform3D:from],[NSValue valueWithCATransform3D:normal],reflow.length ? reflow : animate,NO) forKey:@"bern.reflow"];}}
            BOOL nudgeChanged=![old.nudge isEqual:frame.nudge];BOOL booleanPulse=[frame.nudge isKindOfClass:NSNumber.class] && [frame.nudge boolValue];if(nudgeChanged && (booleanPulse || !BNIsNull(BNDict(frame.element[@"props"])[@"nudge_key"]))){CGFloat scale=BNPropNumber(host,frame.element,@"nudge_scale",frame.locals,1.06);CATransform3D normal=layer.transform,from=CATransform3DConcat(normal,CATransform3DMakeScale(scale,scale,1));[layer addAnimation:BNMotionAnimation(host,@"transform",[NSValue valueWithCATransform3D:from],[NSValue valueWithCATransform3D:normal],animate.length ? animate : @"snappy",NO) forKey:@"bern.nudge"];}
        }
        BNMotionFrame *hero=frame.hero.length ? oldHeroes[frame.hero] : nil;
        if(hero && !frame.reduce && (!CGRectEqualToRect(hero.rect,frame.rect) || ![hero.key isEqual:frame.key])){
            CALayer *overlay=BNMotionOverlay(state,hero);if(overlay){overlay.frame=frame.rect;NSString *token=animate.length ? animate : @"hero";[overlay addAnimation:BNMotionAnimation(host,@"position",BNMotionPoint(CGPointMake(CGRectGetMidX(hero.rect),CGRectGetMidY(hero.rect))),BNMotionPoint(overlay.position),token,NO) forKey:@"bern.hero.position"];[overlay addAnimation:BNMotionAnimation(host,@"bounds",BNMotionRect(CGRectMake(0,0,hero.rect.size.width,hero.rect.size.height)),BNMotionRect(overlay.bounds),token,NO) forKey:@"bern.hero.bounds"];CAPropertyAnimation *fade=BNMotionAnimation(host,@"opacity",@1,@0,token,NO);overlay.opacity=0;[CATransaction begin];[CATransaction setCompletionBlock:^{[overlay removeFromSuperlayer];[state.overlays removeObject:overlay];}];[overlay addAnimation:fade forKey:@"bern.hero.fade"];[CATransaction commit];}
        }else if(!old){NSString *appear=BNPropString(host,frame.element,@"appear",frame.locals);if(appear.length){CGFloat delay=BNPropNumber(host,frame.element,@"appear_delay",frame.locals,0);NSDictionary *parent=BNMeta(view.superview);CGFloat stagger=BNPropNumber(host,BNDict(parent[@"element"]),@"stagger",BNDict(parent[@"locals"]),0);NSUInteger index=[view.superview.subviews indexOfObject:view];if(index!=NSNotFound)delay+=index*stagger;BNMotionTransitionOnLayer(host,layer,frame,appear,YES,frame.reduce ? 0 : delay,nil);}}
    }
    for(BNMotionFrame *old in before.allValues)if(!now[old.key]){NSString *name=BNPropString(host,old.element,@"disappear",old.locals);if(name.length && old.image){CALayer *overlay=BNMotionOverlay(state,old);if(overlay){overlay.opacity=0;BNMotionTransitionOnLayer(host,overlay,old,name,NO,0,^{[overlay removeFromSuperlayer];[state.overlays removeObject:overlay];});}}}
    for(BNWindow *window in host.windows.allValues){BNMotionInitializeReveal(window.root.content);BNMotionRevealChildren(window.root.content);}
    state.previous=now;state.started=YES;
}
static void BNMotionStop(BNHost *host) {BNPopoverPrune(host,YES);BNMotionState *state=objc_getAssociatedObject(host,BNMotionStateKey);for(CALayer *layer in state.overlays)[layer removeFromSuperlayer];objc_setAssociatedObject(host,BNMotionStateKey,nil,OBJC_ASSOCIATION_RETAIN_NONATOMIC);}

static BOOL BNMotionFocused(BNView *view) {
#if TARGET_OS_OSX
    NSResponder *responder=view.window.firstResponder;NSView *focus=[responder isKindOfClass:NSView.class] ? (NSView *)responder : nil;if([focus isKindOfClass:NSTextView.class] && [(NSTextView *)focus isFieldEditor] && [[(NSTextView *)focus delegate] isKindOfClass:NSView.class])focus=(NSView *)[(NSTextView *)focus delegate];return focus && (focus==view || [focus isDescendantOf:view]);
#else
    if(view.isFirstResponder)return YES;for(BNView *child in view.subviews)if(BNMotionFocused(child))return YES;return NO;
#endif
}
static void BNMotionRevealChildren(BNView *view) {
    NSDictionary *meta=BNMeta(view),*element=BNDict(meta[@"element"]),*locals=BNDict(meta[@"locals"]);BNHost *host=[BNHost shared];
    if([BNPropString(host,element,@"reveal",locals) isEqual:@"hover"]){BOOL shown=BNMotionFocused(view);
        for(BNView *ancestor=view.superview;ancestor;ancestor=ancestor.superview){NSDictionary *parent=BNMeta(ancestor);if(parent[@"scopeHovered"]){shown=shown || [parent[@"scopeHovered"] boolValue];break;}}
        NSMutableDictionary *updated=[meta mutableCopy];BOOL before=[meta[@"revealHidden"] boolValue];updated[@"revealHidden"]=@(!shown);BNSetMeta(view,updated);CALayer *layer=BNLayer(view);CGFloat normal=meta[@"styleOpacity"] ? [meta[@"styleOpacity"] doubleValue] : 1;
        if(before==shown){CGFloat from=layer.presentationLayer ? layer.presentationLayer.opacity : layer.opacity;layer.opacity=shown ? normal : 0;[layer addAnimation:BNMotionAnimation(host,@"opacity",@(from),@(layer.opacity),@"smooth",BNMotionReduced(view,host)) forKey:@"bern.reveal"];}else layer.opacity=shown ? normal : 0;
    }
    for(BNView *child in view.subviews)BNMotionRevealChildren(child);
}
static void BNMotionReveal(BNView *view, BOOL shown) {NSMutableDictionary *meta=[BNMeta(view) mutableCopy];meta[@"scopeHovered"]=@(shown);BNSetMeta(view,meta);BNMotionRevealChildren(view);}
static void BNMotionInitializeReveal(BNView *view) {
    if([view isKindOfClass:BNLayout.class]){
        BOOL hovered=NO;
#if TARGET_OS_OSX
        if(view.window){NSPoint point=[view.window convertPointFromScreen:NSEvent.mouseLocation];point=[view convertPoint:point fromView:nil];hovered=NSPointInRect(point,view.bounds);}
#endif
        NSMutableDictionary *meta=[BNMeta(view) mutableCopy];meta[@"scopeHovered"]=@(hovered);BNSetMeta(view,meta);
    }for(BNView *child in view.subviews)BNMotionInitializeReveal(child);
}
static void BNMotionScroll(BNHost *host, BNScroll *scroll) {
    if(!host || !scroll.document)return;NSMutableArray *pending=[NSMutableArray arrayWithArray:scroll.document.subviews];
    while(pending.count){BNView *view=pending.firstObject;[pending removeObjectAtIndex:0];[pending addObjectsFromArray:view.subviews];NSDictionary *meta=BNMeta(view),*element=BNDict(meta[@"element"]),*locals=BNDict(meta[@"locals"]);NSDictionary *props=BNDict(element[@"props"]);if(BNIsNull(props[@"scroll_scale"]) && BNIsNull(props[@"scroll_opacity"]))continue;
        CALayer *layer=BNLayer(view);NSMutableDictionary *updated=[meta mutableCopy];NSValue *baseValue=meta[@"styleTransform"] ?: meta[@"scrollBaseTransform"];if(!baseValue){baseValue=[NSValue valueWithCATransform3D:layer.transform];updated[@"scrollBaseTransform"]=baseValue;}CATransform3D base=baseValue.CATransform3DValue;NSNumber *baseOpacity=meta[@"styleOpacity"] ?: meta[@"scrollBaseOpacity"];if(!baseOpacity){baseOpacity=@(layer.opacity);updated[@"scrollBaseOpacity"]=baseOpacity;}BNSetMeta(view,updated);
        if(BNMotionReduced(view,host)){layer.transform=base;layer.opacity=baseOpacity.floatValue;continue;}
        CGRect rect=[view.superview convertRect:view.frame toView:scroll];CGFloat extent=scroll.horizontal ? scroll.bounds.size.width : scroll.bounds.size.height,center=scroll.horizontal ? CGRectGetMidX(rect) : CGRectGetMidY(rect),item=scroll.horizontal ? rect.size.width : rect.size.height;CGFloat near=1-MIN(1,fabs(center-extent/2)/MAX(1,(extent+item)/2));
        CGFloat target=BNPropNumber(host,element,@"scroll_scale",locals,1),scale=1+(target-1)*near,opacity=BNPropNumber(host,element,@"scroll_opacity",locals,1),anchorX=BNPropNumber(host,element,@"scroll_origin_x",locals,0.5),anchorY=BNPropNumber(host,element,@"scroll_origin_y",locals,0.5);
        CATransform3D effect=CATransform3DMakeTranslation((layer.anchorPoint.x-anchorX)*view.bounds.size.width*(1-scale),(layer.anchorPoint.y-anchorY)*view.bounds.size.height*(1-scale),0);effect=CATransform3DScale(effect,scale,scale,1);layer.transform=CATransform3DConcat(base,effect);layer.opacity=baseOpacity.floatValue*(opacity+(1-opacity)*near);
    }
}
