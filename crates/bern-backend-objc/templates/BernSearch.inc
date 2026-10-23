// Native search fields and palettes. The presentation, text editing and
// scrolling are AppKit/UIKit controls; result content uses the shared renderer.
static BOOL BNMotionReduced(BNView *,BNHost *);
@class BNSearchState;
@interface BNSearchEntry:NSObject
@property(nonatomic,weak)BNControl *control;
@property(nonatomic,strong)NSString *target;
@end
@implementation BNSearchEntry
@end
@interface BNSearchDelegate:NSObject
#if TARGET_OS_OSX
<NSSearchFieldDelegate,NSPopoverDelegate>
#else
<UITextFieldDelegate,UIPopoverPresentationControllerDelegate>
#endif
@property(nonatomic,weak)BNSearchState *state;
-(void)changed:(id)sender;
-(void)close:(id)sender;
@end
@interface BNSearchState:NSObject
@property(nonatomic,weak)BNHost *host;
@property(nonatomic,weak)BNWindow *window;
@property(nonatomic,strong)NSString *key;
@property(nonatomic,strong)NSDictionary *element;
@property(nonatomic,strong)NSDictionary *scope;
@property(nonatomic,strong)NSMutableArray<BNSearchEntry *> *entries;
@property(nonatomic,strong)NSString *selection;
@property(nonatomic,strong)NSString *shownText;
@property(nonatomic,strong)NSString *previousModal;
@property(nonatomic,weak)BNView *trigger;
@property(nonatomic,weak)BNView *input;
@property(nonatomic,weak)BNControl *control;
@property(nonatomic,strong)BNSearchDelegate *delegate;
@property(nonatomic,strong)BNLayout *panel;
@property(nonatomic,strong)BNScroll *scroll;
@property(nonatomic)BOOL palette;
@property(nonatomic)BOOL presented;
@property(nonatomic)BOOL closing;
@property(nonatomic)BOOL editing;
@property(nonatomic)BOOL mounted;
@property(nonatomic,copy)void(^completion)(void);
#if TARGET_OS_OSX
@property(nonatomic,strong)NSPopover *popover;
#else
@property(nonatomic,strong)UIViewController *controller;
#endif
-(NSDictionary *)locals;
-(NSDictionary *)resultScope;
-(NSString *)text;
-(void)edit:(NSString *)text;
-(void)open;
-(void)choose;
-(void)move:(NSInteger)delta;
-(void)closeThen:(void(^)(void))completion;
-(void)closed;
-(void)rebuildPalette;
-(void)normalizeSelection;
@end
static NSMutableDictionary<NSString *,BNSearchState *> *BNSearchStates(BNWindow *window) {
    NSMutableDictionary *states=objc_getAssociatedObject(window,@selector(resultScope));if(!states){states=[NSMutableDictionary dictionary];objc_setAssociatedObject(window,@selector(resultScope),states,OBJC_ASSOCIATION_RETAIN_NONATOMIC);}return states;
}
static BNSearchState *BNSearchForScope(NSDictionary *locals) {BNWindow *window=locals[@"__window"];return window?BNSearchStates(window)[locals[@"__searchKey"]?:@""]:nil;}
static NSString *BNSearchIdentity(NSDictionary *element,NSDictionary *locals) {BNWindow *window=locals[@"__window"];return [NSString stringWithFormat:@"%@#%llu:%@:%@%@",window.identifier,(unsigned long long)window.generation,locals[@"__component"]?:@"",element[@"path"],locals[@"__keys"]?:@""];}
static BOOL BNSearchContentsMounted(BNHost *host,NSDictionary *element,NSDictionary *locals) {
    BNSearchState *state=BNSearchStates(locals[@"__window"])[BNSearchIdentity(element,locals)];if([BNPropString(host,element,@"style",locals) isEqual:@"palette"])return state.presented&&!state.closing;
    return state.editing||BNString([host field:element[@"props"][@"value"][@"field"] locals:locals]).length>0;
}
static BNSearchState *BNSearchModel(BNHost *host,NSDictionary *element,NSDictionary *locals) {
    BNWindow *window=locals[@"__window"];NSString *key=BNSearchIdentity(element,locals);BNSearchState *state=BNSearchStates(window)[key];if(!state){state=[BNSearchState new];state.entries=[NSMutableArray array];state.key=key;state.window=window;state.host=host;state.delegate=[BNSearchDelegate new];state.delegate.state=state;BNSearchStates(window)[key]=state;}
    state.element=element;NSMutableDictionary *scope=[locals mutableCopy];[scope removeObjectForKey:@"__window"];state.scope=scope;state.palette=[BNPropString(host,element,@"style",locals) isEqual:@"palette"];state.mounted=YES;
    NSString *text=[state text];if(![state.shownText isEqual:text]){state.selection=nil;state.shownText=text;}return state;
}
static NSString *BNSearchNormalizeKey(NSString *key) {
#if TARGET_OS_OSX
    if([key isEqual:[NSString stringWithFormat:@"%C",(unichar)NSUpArrowFunctionKey]])return @"up";
    if([key isEqual:[NSString stringWithFormat:@"%C",(unichar)NSDownArrowFunctionKey]])return @"down";
#else
    if([key isEqual:UIKeyInputUpArrow])return @"up";if([key isEqual:UIKeyInputDownArrow])return @"down";
#endif
    if([key isEqual:@"\r"]||[key isEqual:@"\n"])return @"return";if([key isEqual:@"\033"])return @"escape";return key;
}
static BOOL BNSearchKey(BNSearchState *state,NSString *input) {
    @try {
#if TARGET_OS_OSX
    if([((NSTextField *)state.input).currentEditor isKindOfClass:NSTextView.class]&&[(NSTextView *)((NSTextField *)state.input).currentEditor hasMarkedText])return NO;
#else
    if(((UITextField *)state.input).markedTextRange)return NO;
#endif
    NSString *key=BNSearchNormalizeKey(input);if([key isEqual:@"up"]){[state move:-1];return YES;}if([key isEqual:@"down"]){[state move:1];return YES;}if([key isEqual:@"return"]){[state choose];return YES;}if([key isEqual:@"escape"]){if(state.palette)[state closeThen:nil];else[state edit:@""];return YES;}return NO;
    }@catch(NSException *problem){[state.host showError:problem.reason];return YES;}
}
#if !TARGET_OS_OSX
@interface BNSearchNativeField:UISearchTextField
@property(nonatomic,weak)BNSearchState *searchState;
@end
@implementation BNSearchNativeField
-(NSArray<UIKeyCommand *> *)keyCommands {NSMutableArray *keys=[[super keyCommands] mutableCopy]?:[NSMutableArray array];for(NSString *input in @[UIKeyInputUpArrow,UIKeyInputDownArrow,@"\r",@"\033"])[keys addObject:[UIKeyCommand keyCommandWithInput:input modifierFlags:0 action:@selector(bnSearchKey:)]];return keys;}
-(void)bnSearchKey:(UIKeyCommand *)command{BNSearchKey(_searchState,command.input);}
@end
#endif
static BNFont *BNSearchFont(BNSearchState *state) {
    // Search.style selects its presentation, rather than a typography token.
    NSMutableDictionary *element=[state.element mutableCopy],*props=[BNDict(element[@"props"]) mutableCopy];[props removeObjectForKey:@"style"];element[@"props"]=props;return BNTextFont(state.host,element,state.locals);
}
static BNView *BNSearchInput(BNSearchState *state,NSString *prompt) {
#if TARGET_OS_OSX
    NSSearchField *field=[[NSSearchField alloc]initWithFrame:CGRectZero];field.placeholderString=prompt;field.stringValue=[state text];field.delegate=state.delegate;field.target=state.delegate;field.action=@selector(changed:);field.font=BNSearchFont(state);
#else
    BNSearchNativeField *field=[[BNSearchNativeField alloc]initWithFrame:CGRectZero];field.searchState=state;field.placeholder=prompt;field.text=[state text];field.delegate=state.delegate;field.returnKeyType=UIReturnKeySearch;field.font=BNSearchFont(state);[field addTarget:state.delegate action:@selector(changed:) forControlEvents:UIControlEventEditingChanged];
#endif
    field.accessibilityLabel=prompt;BNSetMeta(field,@{@"fillWidth":@YES,@"minimumSize":@[@160,@34]});state.input=field;return field;
}
static void BNSearchUpdateText(BNSearchState *state) {NSString *text=state.text;
#if TARGET_OS_OSX
    NSTextField *field=(NSTextField *)state.input;if(![field.stringValue isEqual:text]){NSTextView *editor=(NSTextView *)field.currentEditor;if(!editor||![editor hasMarkedText])field.stringValue=text;}
#else
    UITextField *field=(UITextField *)state.input;if(![field.text isEqual:text]&&!field.markedTextRange)field.text=text;
#endif
}
static void BNSearchFocus(BNSearchState *state) {
#if TARGET_OS_OSX
    [state.input.window makeFirstResponder:state.input];
#else
    [state.input becomeFirstResponder];
#endif
}
@implementation BNSearchDelegate
-(void)changed:(id)sender {
#if TARGET_OS_OSX
    NSString *text=[sender isKindOfClass:NSNotification.class]?((NSTextField *)[sender object]).stringValue:((NSTextField *)sender).stringValue;
#else
    NSString *text=((UITextField *)sender).text?:@"";
#endif
    @try{[_state edit:text];}@catch(NSException *problem){[_state.host showError:problem.reason];}
}
-(void)close:(id)sender{[_state closeThen:nil];}
#if TARGET_OS_OSX
-(void)controlTextDidChange:(NSNotification *)note{[self changed:note];}
-(void)controlTextDidBeginEditing:(NSNotification *)note{_state.editing=YES;[_state.host scheduleRender];}
-(void)controlTextDidEndEditing:(NSNotification *)note{if(!_state.host.rendering&&!_state.palette){_state.editing=NO;[_state.host scheduleRender];}}
-(BOOL)control:(NSControl *)control textView:(NSTextView *)view doCommandBySelector:(SEL)selector {if(selector==@selector(moveUp:))return BNSearchKey(_state,@"up");if(selector==@selector(moveDown:))return BNSearchKey(_state,@"down");if(selector==@selector(insertNewline:))return BNSearchKey(_state,@"return");if(selector==@selector(cancelOperation:))return BNSearchKey(_state,@"escape");return NO;}
-(void)popoverDidClose:(NSNotification *)note{[_state closed];}
#else
-(void)textFieldDidBeginEditing:(UITextField *)field{_state.editing=YES;[_state.host scheduleRender];}
-(void)textFieldDidEndEditing:(UITextField *)field{if(!_state.host.rendering&&!_state.palette){_state.editing=NO;[_state.host scheduleRender];}}
-(BOOL)textFieldShouldReturn:(UITextField *)field{return BNSearchKey(_state,@"return");}
-(UIModalPresentationStyle)adaptivePresentationStyleForPresentationController:(UIPresentationController *)controller{return UIModalPresentationNone;}
-(void)presentationControllerDidDismiss:(UIPresentationController *)controller{[_state closed];}
#endif
@end
@implementation BNSearchState
-(NSDictionary *)locals{NSMutableDictionary *scope=[_scope mutableCopy]?:[NSMutableDictionary dictionary];if(_window)scope[@"__window"]=_window;return scope;}
-(NSDictionary *)resultScope{NSMutableDictionary *scope=[[self locals] mutableCopy];scope[@"__searchKey"]=_key;if(_palette)scope[@"__modal"]=_key;return scope;}
-(NSString *)text{return BNString([_host field:_element[@"props"][@"value"][@"field"] locals:[self locals]]);}
-(void)edit:(NSString *)text{if(![text isEqual:[self text]]){_selection=nil;[_host setField:_element[@"props"][@"value"][@"field"] value:text locals:[self locals]];}BNSearchUpdateText(self);}
-(void)normalizeSelection {
    NSMutableArray<BNSearchEntry *> *entries=[NSMutableArray array];for(BNSearchEntry *entry in _entries)if(entry.control&&entry.control.enabled)[entries addObject:entry];_entries=entries;
    BOOL found=NO;for(BNSearchEntry *entry in entries)if([entry.target isEqual:_selection]){found=YES;break;}if(!found)_selection=entries.firstObject.target;
    for(BNSearchEntry *entry in entries){BNView *view=entry.control.view;BOOL selected=[entry.target isEqual:_selection];
#if TARGET_OS_OSX
        BNColor *color=[NSColor colorWithSRGBRed:120.0/255 green:120.0/255 blue:128.0/255 alpha:selected?(BNDark(view)?0.24:0.14):0];view.accessibilitySelected=selected;
#else
        BNColor *color=[UIColor colorWithRed:120.0/255 green:120.0/255 blue:128.0/255 alpha:selected?(BNDark(view)?0.24:0.14):0];if(selected)view.accessibilityTraits|=UIAccessibilityTraitSelected;else view.accessibilityTraits&=~UIAccessibilityTraitSelected;
#endif
        BNLayer(view).backgroundColor=color.CGColor;BNLayer(view).cornerRadius=8;
    }
}
-(void)move:(NSInteger)delta {
    [self normalizeSelection];if(!_entries.count||_closing)return;NSInteger old=0;for(NSUInteger i=0;i<_entries.count;i++)if([_entries[i].target isEqual:_selection])old=(NSInteger)i;NSInteger next=MIN((NSInteger)_entries.count-1,MAX(0,old+delta));_selection=_entries[(NSUInteger)next].target;[self normalizeSelection];BNView *view=_entries[(NSUInteger)next].control.view;
#if TARGET_OS_OSX
    [view scrollRectToVisible:view.bounds];
#else
    for(UIView *parent=view.superview;parent;parent=parent.superview)if([parent isKindOfClass:UIScrollView.class]){[(UIScrollView *)parent scrollRectToVisible:[view convertRect:view.bounds toView:parent] animated:!BNMotionReduced(view,_host)];break;}
#endif
}
-(void)choose {
    if(_closing)return;[self normalizeSelection];for(BNSearchEntry *entry in _entries)if([entry.target isEqual:_selection]){[_host performControl:entry.control event:@"activate" value:BNNull()];return;}
    if(!_palette)BNFire(_host,_element,[self locals],_input);
}
-(void)rebuildPalette {
    if(!_presented||_closing)return;[_entries removeAllObjects];NSDictionary *scope=[self resultScope];BNSearchUpdateText(self);
    BNLayout *document=BNContainer(@"column",0);document.fillWidth=YES;for(BNView *view in BNRendered(_host,_element[@"children"],scope))[document addSubview:view];[_scroll.document removeFromSuperview];_scroll.document=document;[self normalizeSelection];
    _control.view=_input;_control.locals=scope;_window.modalKey=_key;
    CGFloat width=MIN(BNPropNumber(_host,_element,@"width",self.locals,640),MAX(280,_window.root.bounds.size.width-32)),maximum=MIN(BNPropNumber(_host,_element,@"height",self.locals,480),MAX(120,_window.root.bounds.size.height-64));CGSize result=[document measure:CGSizeMake(MAX(1,width-24),100000)];CGFloat height=MIN(maximum,MAX(58,result.height+58));
    _panel.frame=CGRectMake(0,0,width,height);[_panel arrange];
#if TARGET_OS_OSX
    _popover.contentSize=CGSizeMake(width,height);
#else
    _controller.preferredContentSize=CGSizeMake(width,height);
#endif
}
-(void)open {
    if(!_palette){_editing=YES;BNSearchFocus(self);[_host scheduleRender];return;}if(_presented){BNSearchFocus(self);return;}if(!_trigger.window||!_host.handle)return;
    _presented=YES;_closing=NO;_selection=nil;_previousModal=_window.modalKey;[self edit:@""];
    NSString *prompt=BNPropString(_host,_element,@"panel_prompt",self.locals);if(!prompt.length)prompt=BNPropString(_host,_element,@"prompt",self.locals);
    _panel=BNContainer(@"column",8);_panel.padding=12;_panel.fillWidth=YES;_panel.fillHeight=YES;BNLayout *header=BNContainer(@"row",8);header.fillWidth=YES;[header addSubview:BNSearchInput(self,prompt)];
#if TARGET_OS_OSX
    NSButton *close=[NSButton buttonWithTitle:@"" target:_delegate action:@selector(close:)];close.image=[NSImage imageWithSystemSymbolName:@"xmark" accessibilityDescription:BNMediaText(@"bern.window.close")];close.bordered=NO;
#else
    UIButton *close=[UIButton buttonWithType:UIButtonTypeSystem];[close setImage:[UIImage systemImageNamed:@"xmark"] forState:UIControlStateNormal];[close addTarget:_delegate action:@selector(close:) forControlEvents:UIControlEventTouchUpInside];
#endif
    close.accessibilityLabel=BNMediaText(@"bern.window.close");BNSetMeta(close,@{@"width":@28,@"height":@28});[header addSubview:close];[_panel addSubview:header];_scroll=[[BNScroll alloc]initWithFrame:CGRectZero];_scroll.host=_host;_scroll.indicators=YES;BNSetMeta(_scroll,@{@"fillWidth":@YES,@"fillHeight":@YES,@"grow":@YES});[_panel addSubview:_scroll];
#if TARGET_OS_OSX
    NSViewController *controller=[NSViewController new];controller.view=_panel;_popover=[NSPopover new];_popover.behavior=NSPopoverBehaviorTransient;_popover.contentViewController=controller;_popover.delegate=_delegate;_popover.animates=!BNMotionReduced(_trigger,_host);[self rebuildPalette];[_popover showRelativeToRect:_trigger.bounds ofView:_trigger preferredEdge:NSRectEdgeMaxY];
#else
    _controller=[UIViewController new];_controller.view=_panel;_controller.view.backgroundColor=UIColor.systemBackgroundColor;_controller.modalPresentationStyle=UIModalPresentationPopover;UIPopoverPresentationController *popover=_controller.popoverPresentationController;popover.sourceView=_trigger;popover.sourceRect=_trigger.bounds;popover.delegate=_delegate;[self rebuildPalette];UIViewController *presenter=_trigger.window.rootViewController;while(presenter.presentedViewController)presenter=presenter.presentedViewController;__weak BNSearchState *weak=self;[presenter presentViewController:_controller animated:!BNMotionReduced(_trigger,_host) completion:^{BNSearchFocus(weak);}];
#endif
    BNSearchFocus(self);[_host scheduleRender];
}
-(void)closeThen:(void(^)(void))completion {
    if(!_palette){if(completion)completion();return;}if(!_presented||_closing)return;_closing=YES;_completion=[completion copy];
#if TARGET_OS_OSX
    [_popover close];[self closed];
#else
    if(_controller.presentingViewController){__weak BNSearchState *weak=self;[_controller dismissViewControllerAnimated:!BNMotionReduced(_input,_host) completion:^{[weak closed];}];}else[self closed];
#endif
}
-(void)closed {
    if(!_presented&&!_closing)return;_presented=NO;_closing=NO;void(^completion)(void)=_completion;_completion=nil;[_entries removeAllObjects];_selection=nil;
    if([_window.modalKey isEqual:_key])_window.modalKey=_window.modalLayers.lastObject[@"key"]?:_previousModal;_control.view=_trigger;_control.locals=self.locals;
    NSMutableArray *remaining=[NSMutableArray array];for(BNControl *control in _host.controls)if(![control.locals[@"__searchKey"] isEqual:_key]||control==_control)[remaining addObject:control];_host.controls=remaining;
    _panel=nil;_scroll=nil;_input=nil;
#if TARGET_OS_OSX
    _popover=nil;
#else
    _controller=nil;
#endif
    __weak BNSearchState *weak=self;__weak BNHost *weakHost=_host;[_host scheduleRender];dispatch_async(dispatch_get_main_queue(),^{BNSearchState *state=weak;BNHost *host=weakHost;if(!host.handle)return;
#if TARGET_OS_OSX
        if(state.trigger.window)[state.trigger.window makeFirstResponder:state.trigger];
#else
        if(state.trigger.window)[state.trigger becomeFirstResponder];
#endif
        @try{if(completion)completion();}@catch(NSException *problem){[host showError:problem.reason];}});
}
@end

static BOOL BNSearchBeforeFire(BNHost *host,NSDictionary *element,NSDictionary *locals,BNView *view) {
    if(![element[@"kind"] isEqual:@"SearchItem"]||[locals[@"__searchCommitted"] boolValue])return NO;BNSearchState *state=BNSearchForScope(locals);if(!state||!state.palette||!state.presented)return NO;if(state.closing)return YES;
    NSMutableDictionary *scope=[locals mutableCopy];scope[@"__searchCommitted"]=@YES;__weak BNView *anchor=view;[state closeThen:^{if(host.handle)BNFire(host,element,scope,anchor);}];return YES;
}
static void BNSearchResultRow(BNHost *host,BNControl *control,NSDictionary *element,NSDictionary *locals) {
    if(BNArray(element[@"children"]).count||![control.view isKindOfClass:BNStyledButton.class])return;
    BNLayout *row=BNContainer(@"row",12);row.fillWidth=YES;row.paddingX=12;row.requestedHeight=42;row.alignment=@"center";
    NSString *icon=BNPropString(host,element,@"icon",locals);if(icon.length){
#if TARGET_OS_OSX
        NSImageView *image=[[NSImageView alloc]initWithFrame:CGRectZero];image.image=[NSImage imageWithSystemSymbolName:icon accessibilityDescription:nil];image.imageScaling=NSImageScaleProportionallyDown;image.contentTintColor=BNRole(@"text.secondary");image.accessibilityElement=NO;
#else
        UIImageView *image=[[UIImageView alloc]initWithImage:[UIImage systemImageNamed:icon]];image.contentMode=UIViewContentModeCenter;image.tintColor=BNRole(@"text.secondary");image.isAccessibilityElement=NO;
#endif
        BNSetMeta(image,@{@"width":@26,@"height":@26});BNLayer(image).cornerRadius=7;BNLayer(image).backgroundColor=BNRole(@"fill.subtle").CGColor;[row addSubview:image];
    }
    for(NSString *name in @[@"label",@"detail",@"hint"]){NSString *text=BNPropString(host,element,name,locals);if([name isEqual:@"hint"]){BNView *spacer=[[BNView alloc]initWithFrame:CGRectZero];BNSetMeta(spacer,@{@"fillWidth":@YES,@"grow":@YES});[row addSubview:spacer];}if(!text.length)continue;
        BOOL title=[name isEqual:@"label"];NSDictionary *props=@{@"font_size":@{@"kind":@"number",@"value":title?@13:@11.5},@"emphasis":@{@"kind":@"keyword",@"value":title?@"primary":[name isEqual:@"detail"]?@"secondary":@"tertiary"}};BNView *label=BNLabel(host,text,@{@"props":props},locals);
#if TARGET_OS_OSX
        ((NSTextField *)label).selectable=NO;((NSTextField *)label).maximumNumberOfLines=1;
#else
        ((UILabel *)label).numberOfLines=1;label.userInteractionEnabled=NO;
#endif
        [row addSubview:label];
    }
    ((BNStyledButton *)control.view).customContent=row;NSMutableDictionary *meta=[BNMeta(control.view) mutableCopy];meta[@"fillWidth"]=@YES;meta[@"minimumSize"]=@[@0,@42];BNSetMeta(control.view,meta);
}
static void BNSearchRegisterResult(BNHost *host,NSDictionary *element,NSDictionary *locals,BNView *view) {
    if(![element[@"kind"] isEqual:@"SearchItem"])return;BNSearchState *state=BNSearchForScope(locals);if(!state)return;
    for(BNControl *control in [host.controls reverseObjectEnumerator])if(control.element==element&&control.locals[@"__window"]==locals[@"__window"]&&[BNString(control.locals[@"__component"]) isEqual:BNString(locals[@"__component"])]&&[BNString(control.locals[@"__keys"]) isEqual:BNString(locals[@"__keys"])]){
        BNSearchResultRow(host,control,element,locals);
        if(state.palette){void(^activate)(void)=[control.activate copy];void(^setFile)(NSURL *)=[control.setFile copy];__weak BNSearchState *weak=state;
            control.activate=^{BNSearchState *owner=weak;if(!owner||owner.closing)return;[owner closeThen:^{if(!host.handle)return;if(setFile)BNChooseFile(host,element,locals,owner.trigger,^(NSURL *url){setFile(url);});else if(activate)activate();}];};
            if(setFile)control.setFile=^(NSURL *url){BNSearchState *owner=weak;if(owner&&!owner.closing)[owner closeThen:^{if(host.handle)setFile(url);}];};
        }
        if(control.enabled&&BNPropBool(host,element,@"navigation",locals,YES)){BNSearchEntry *entry=[BNSearchEntry new];entry.control=control;entry.target=control.target;[state.entries addObject:entry];}break;
    }
}
static BNView *BNRenderSearch(BNHost *host,NSDictionary *element,NSDictionary *locals) {
    BNSearchState *state=BNSearchModel(host,element,locals);NSString *prompt=BNPropString(host,element,@"prompt",locals);BNControl *control=[host registerControl:element view:nil role:@"search" label:prompt locals:locals];state.control=control;__weak BNSearchState *weak=state;control.edit=^(NSString *text){[weak edit:text];};control.submit=^{[weak choose];};control.value=^{return [weak text];};control.focus=^{[weak open];};
    if(state.palette){control.activate=^{[weak open];};BNView *trigger=state.trigger;if(!trigger)trigger=BNMakeButton(prompt,@"magnifyingglass",control,YES);else{
#if TARGET_OS_OSX
        ((NSButton *)trigger).title=prompt;((NSButton *)trigger).target=control;
#else
        [(UIButton *)trigger setTitle:prompt forState:UIControlStateNormal];[(UIButton *)trigger removeTarget:nil action:@selector(clicked:) forControlEvents:UIControlEventTouchUpInside];[(UIButton *)trigger addTarget:control action:@selector(clicked:) forControlEvents:UIControlEventTouchUpInside];
#endif
        BNKeep(trigger,control);
    }state.trigger=trigger;control.view=trigger;BNSetMeta(trigger,@{@"width":@250,@"height":@34,@"minimumSize":@[@250,@34]});BNLayer(trigger).cornerRadius=17;BNLayer(trigger).backgroundColor=BNRole(@"fill.subtle").CGColor;if(state.presented)[state rebuildPalette];return trigger;}
    NSString *current=state.text;BNView *input=state.input?:BNSearchInput(state,prompt);BNSearchUpdateText(state);control.view=input;
#if TARGET_OS_OSX
    ((NSTextField *)input).placeholderString=prompt;((NSTextField *)input).font=BNSearchFont(state);((NSTextField *)input).enabled=control.enabled;
#else
    ((UITextField *)input).placeholder=prompt;((UITextField *)input).font=BNSearchFont(state);((UITextField *)input).enabled=control.enabled;
#endif
    BNLayout *column=BNContainer(@"column",0);column.fillWidth=YES;[column addSubview:input];NSMutableDictionary *size=[BNMeta(input) mutableCopy];for(NSString *name in @[@"width",@"height"]){[size removeObjectForKey:name];id value=[host prop:element name:name locals:locals];if(!BNIsNull(value))size[name]=value;}BNSetMeta(input,size);
    if(state.editing||current.length){for(BNView *result in BNRendered(host,element[@"children"],state.resultScope))[column addSubview:result];}BNSetMeta(column,@{@"fillWidth":@YES});return column;
}
static void BNSearchBeginRender(BNHost *host) {for(BNWindow *window in host.windows.allValues)for(BNSearchState *state in BNSearchStates(window).allValues){state.mounted=NO;[state.entries removeAllObjects];}}
static void BNSearchEndRender(BNHost *host) {for(BNWindow *window in host.windows.allValues)for(NSString *key in [BNSearchStates(window).allKeys copy]){BNSearchState *state=BNSearchStates(window)[key];if(!state.mounted){state.completion=nil;[state closeThen:nil];[BNSearchStates(window)removeObjectForKey:key];}else{[state normalizeSelection];if(state.presented)window.modalKey=state.key;}}}
static void BNSearchWindowClosed(BNWindow *window) {for(BNSearchState *state in BNSearchStates(window).allValues){state.completion=nil;
#if TARGET_OS_OSX
    [state.popover close];
#else
    [state.controller dismissViewControllerAnimated:NO completion:nil];
#endif
    [state closed];} [BNSearchStates(window)removeAllObjects];}
static void BNSearchStop(BNHost *host) {for(BNWindow *window in host.windows.allValues)BNSearchWindowClosed(window);}
static BOOL BNHandleSearchKey(BNHost *host,BNWindow *window,NSString *input) {for(BNSearchState *state in BNSearchStates(window).allValues){if(state.presented)return BNSearchKey(state,input);
#if TARGET_OS_OSX
    if(state.input&&state.input.window.firstResponder==((NSTextField *)state.input).currentEditor)return BNSearchKey(state,input);
#else
    if(state.input.isFirstResponder)return BNSearchKey(state,input);
#endif
}return NO;}
#if !TARGET_OS_OSX
static NSArray<UIKeyCommand *> *BNSearchKeyCommands(BNHost *host,BNWindow *window) {BOOL active=NO;for(BNSearchState *state in BNSearchStates(window).allValues)if(state.presented||state.input.isFirstResponder){active=YES;break;}if(!active)return @[];NSMutableArray *keys=[NSMutableArray array];for(NSString *input in @[UIKeyInputUpArrow,UIKeyInputDownArrow,@"\r",@"\033"])[keys addObject:[UIKeyCommand keyCommandWithInput:input modifierFlags:0 action:@selector(bnSearchKey:)]];return keys;}
@implementation BNRootView (SearchKeys)
-(void)bnSearchKey:(UIKeyCommand *)command{BNHandleSearchKey([BNHost shared],self.context,command.input);}
@end
#endif
