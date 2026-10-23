// Standard platform navigation/tab containers. Declarative page content keeps
// using Bern's shared layout, while AppKit/UIKit own chrome and interaction.
static const void *BNNativeContainersKey=&BNNativeContainersKey;
static NSString *BNContainerIdentity(NSDictionary *element,NSDictionary *locals) {return [NSString stringWithFormat:@"%@/%@%@",locals[@"__component"]?:@"",element[@"path"]?:@"",locals[@"__keys"]?:@""];}
static NSMapTable *BNNativeContainers(BNWindow *window) {NSMapTable *cache=objc_getAssociatedObject(window,BNNativeContainersKey);if(!cache){cache=[NSMapTable strongToWeakObjectsMapTable];objc_setAssociatedObject(window,BNNativeContainersKey,cache,OBJC_ASSOCIATION_RETAIN_NONATOMIC);}return cache;}
static BNLayout *BNNativePage(BNHost *host,NSArray *nodes,NSDictionary *scope) {BNLayout *page=BNContainer(@"column",8);page.fillWidth=YES;page.fillHeight=YES;for(BNView *child in BNRendered(host,nodes,scope))[page addSubview:child];return page;}
static void BNContainerFill(BNView *view){BNSetMeta(view,@{@"fillWidth":@YES,@"fillHeight":@YES,@"grow":@YES,@"minimumSize":@[@120,@100]});}
#if TARGET_OS_OSX
@interface BNNativeTabs:NSTabView<NSTabViewDelegate>
@property(nonatomic,weak)BNHost *host;
@property(nonatomic,strong)NSDictionary *field;
@property(nonatomic,strong)NSDictionary *scope;
@property(nonatomic,strong)NSArray *choices;
@property(nonatomic)BOOL updating;
@end
@implementation BNNativeTabs
-(instancetype)initWithFrame:(NSRect)frame{if((self=[super initWithFrame:frame])){self.delegate=self;self.tabViewType=NSTopTabsBezelBorder;}return self;}
-(BOOL)isFlipped{return YES;}
-(void)layout{[super layout];NSTabViewItem *item=self.selectedTabViewItem;if(item.view){item.view.frame=self.contentRect;if([item.view isKindOfClass:BNLayout.class])[(BNLayout *)item.view arrange];}}
-(void)tabView:(NSTabView *)tabView didSelectTabViewItem:(NSTabViewItem *)item{if(_updating)return;NSUInteger index=[self.tabViewItems indexOfObject:item];if(index<_choices.count)[_host setField:_field value:_choices[index] locals:_scope];}
@end
#else
@interface BNNativePageController:UIViewController
-(void)setPage:(BNLayout *)page;
@end
@implementation BNNativePageController
-(void)loadView{BNLayout *page=BNContainer(@"column",8);page.fillWidth=YES;page.fillHeight=YES;page.backgroundColor=UIColor.systemBackgroundColor;self.view=page;self.edgesForExtendedLayout=UIRectEdgeNone;}
-(void)setPage:(BNLayout *)page{[self loadViewIfNeeded];for(UIView *child in [self.view.subviews copy])[child removeFromSuperview];[self.view addSubview:page];page.frame=self.view.bounds;[self.view setNeedsLayout];}
-(void)viewDidLayoutSubviews{[super viewDidLayoutSubviews];if([self.view isKindOfClass:BNLayout.class])[(BNLayout *)self.view arrange];BNMediaResizeTree(self.view);}
@end
@interface BNNativeControllerView:UIView
@property(nonatomic,strong)UIViewController *controller;
@property(nonatomic,weak)UIViewController *owner;
-(void)attach;
@end
@implementation BNNativeControllerView
-(void)attach{if(!self.window)return;UIResponder *responder=self.nextResponder;while(responder&&![responder isKindOfClass:UIViewController.class])responder=responder.nextResponder;UIViewController *parent=(UIViewController *)responder;if(!parent||parent==_controller||_owner==parent)return;
    if(_owner){[_controller willMoveToParentViewController:nil];[_controller.view removeFromSuperview];[_controller removeFromParentViewController];}
    [parent addChildViewController:_controller];[self addSubview:_controller.view];_controller.view.frame=self.bounds;_controller.view.autoresizingMask=UIViewAutoresizingFlexibleWidth|UIViewAutoresizingFlexibleHeight;[_controller didMoveToParentViewController:parent];_owner=parent;}
-(void)didMoveToWindow{[super didMoveToWindow];if(self.window)[self attach];else if(_owner){[_controller willMoveToParentViewController:nil];[_controller.view removeFromSuperview];[_controller removeFromParentViewController];_owner=nil;}}
-(void)layoutSubviews{[super layoutSubviews];[self attach];_controller.view.frame=self.bounds;[_controller.view setNeedsLayout];[_controller.view layoutIfNeeded];}
-(CGSize)sizeThatFits:(CGSize)size{return size;}
@end
@interface BNNativeTabs:BNNativeControllerView<UITabBarControllerDelegate>
@property(nonatomic,weak)BNHost *host;
@property(nonatomic,strong)NSDictionary *field;
@property(nonatomic,strong)NSDictionary *scope;
@property(nonatomic,strong)NSArray *choices;
@property(nonatomic)BOOL updating;
@end
@implementation BNNativeTabs
-(instancetype)initWithFrame:(CGRect)frame{if((self=[super initWithFrame:frame])){UITabBarController *tabs=[UITabBarController new];tabs.delegate=self;self.controller=tabs;}return self;}
-(void)tabBarController:(UITabBarController *)controller didSelectViewController:(UIViewController *)selected{if(_updating)return;NSUInteger index=[controller.viewControllers indexOfObject:selected];if(index<_choices.count)[_host setField:_field value:_choices[index] locals:_scope];}
@end
@interface BNNativeNavigation:BNNativeControllerView<UINavigationControllerDelegate,UIGestureRecognizerDelegate>
@property(nonatomic,weak)BNHost *host;
@property(nonatomic,strong)NSDictionary *field;
@property(nonatomic,strong)NSDictionary *scope;
@property(nonatomic,strong)NSArray *path;
@property(nonatomic)BOOL updating;
@property(nonatomic)BOOL interacting;
@end
@implementation BNNativeNavigation
-(instancetype)initWithFrame:(CGRect)frame{if((self=[super initWithFrame:frame])){UINavigationController *navigation=[[UINavigationController alloc]initWithRootViewController:[BNNativePageController new]];navigation.delegate=self;self.controller=navigation;}return self;}
-(void)startTransition{if(!_interacting){_interacting=YES;[_host beginInteraction];}}
-(void)finishTransition{if(_interacting){_interacting=NO;[_host endInteraction];}}
-(void)navigationController:(UINavigationController *)navigation willShowViewController:(UIViewController *)controller animated:(BOOL)animated{if(_updating)return;if(animated){[self startTransition];__weak BNNativeNavigation *weakSelf=self;id<UIViewControllerTransitionCoordinator> transition=navigation.transitionCoordinator;[transition animateAlongsideTransition:nil completion:^(id<UIViewControllerTransitionCoordinatorContext> context){[weakSelf finishTransition];}];}}
-(void)navigationController:(UINavigationController *)navigation didShowViewController:(UIViewController *)controller animated:(BOOL)animated{if(!_updating){NSUInteger count=navigation.viewControllers.count?navigation.viewControllers.count-1:0;if(count<_path.count){NSArray *path=[_path subarrayWithRange:NSMakeRange(0,count)];[_host setField:_field value:path locals:_scope];}_path=[BNArray([_host field:_field locals:_scope]) copy];}[self finishTransition];}
@end
static BNView *BNRenderNativeNavigation(BNHost *host,NSDictionary *element,NSDictionary *locals){BNWindow *window=locals[@"__window"];NSString *key=BNContainerIdentity(element,locals);BNNativeNavigation *view=[BNNativeContainers(window)objectForKey:key];if(![view isKindOfClass:BNNativeNavigation.class]){view=[[BNNativeNavigation alloc]initWithFrame:CGRectZero];[BNNativeContainers(window)setObject:view forKey:key];}
    view.host=host;view.field=BNDict(element[@"props"][@"path"])[@"field"];view.scope=locals;NSArray *path=BNArray([host field:view.field locals:locals]);UINavigationController *navigation=(UINavigationController *)view.controller;NSArray *old=navigation.viewControllers;NSMutableArray *controllers=[NSMutableArray array];NSMutableDictionary *scope=[locals mutableCopy];if(view.field)scope[@"__path"]=view.field;
    NSArray *descriptors=BNDescriptors(host,element[@"children"],scope);NSMutableArray *root=[NSMutableArray array],*destinations=[NSMutableArray array];for(NSDictionary *entry in descriptors)if([entry[@"element"][@"kind"] isEqual:@"Destination"])[destinations addObject:entry];else[root addObject:entry];
    for(NSUInteger depth=0;depth<=path.count;depth++){BOOL same=depth==0||(depth<=view.path.count&&[path[depth-1] isEqual:view.path[depth-1]]);BNNativePageController *controller=same&&depth<old.count&&[old[depth] isKindOfClass:BNNativePageController.class]?old[depth]:[BNNativePageController new];[controllers addObject:controller];BOOL active=depth==path.count;
        if(!active&&controller.isViewLoaded&&controller.view.subviews.count)continue;
        NSUInteger controlCount=host.controls.count,modalCount=window.modalLayers.count;NSString *modal=window.modalKey;BNLayout *page=BNContainer(@"column",8);page.fillWidth=YES;page.fillHeight=YES;
        if(depth==0){for(NSDictionary *entry in root){BNView *child=[host renderElement:entry[@"element"] locals:entry[@"locals"]];if(child)[page addSubview:child];}}
        else for(NSDictionary *entry in destinations){NSMutableDictionary *inner=[entry[@"locals"] mutableCopy];NSString *var=BNDict(entry[@"element"][@"template"])[@"var"];if(var)inner[var]=path[depth-1];for(BNView *child in BNRendered(host,entry[@"element"][@"children"],inner))[page addSubview:child];}
        [controller setPage:page];controller.edgesForExtendedLayout=UIRectEdgeNone;controller.title=depth==0?@"":BNString([host prop:element name:@"label" locals:scope]);
        if(!active){while(host.controls.count>controlCount)[host.controls removeLastObject];while(window.modalLayers.count>modalCount)[window.modalLayers removeLastObject];window.modalKey=modal;}
    }
    view.updating=YES;[navigation setViewControllers:controllers animated:NO];view.updating=NO;view.path=[path copy];navigation.navigationBar.tintColor=host.accentColor;
    BNControl *control=[host registerControl:element view:view role:@"navigation" label:BNPropString(host,element,@"label",locals) locals:locals];__weak BNHost *weakHost=host;NSDictionary *field=view.field;control.back=^BOOL{NSMutableArray *current=[BNArray([weakHost field:field locals:locals])mutableCopy];if(!current.count)return NO;[current removeLastObject];return [weakHost setField:field value:current locals:locals];};BNContainerFill(view);return view;
}
#endif
static BNView *BNRenderNativeTabs(BNHost *host,NSDictionary *element,NSDictionary *locals){BNWindow *window=locals[@"__window"];NSString *key=BNContainerIdentity(element,locals);BNNativeTabs *view=[BNNativeContainers(window)objectForKey:key];if(![view isKindOfClass:BNNativeTabs.class]){view=[[BNNativeTabs alloc]initWithFrame:CGRectZero];[BNNativeContainers(window)setObject:view forKey:key];}
    view.host=host;view.field=BNDict(element[@"props"][@"selection"])[@"field"];view.scope=locals;id current=[host field:view.field locals:locals];NSMutableArray *entries=[NSMutableArray array],*accessories=[NSMutableArray array],*choices=[NSMutableArray array],*names=[NSMutableArray array];NSDictionary *definition=[host typeNamed:BNString(BNDict(view.field[@"type"])[@"name"]) list:@"enums"];
    for(NSDictionary *entry in BNDescriptors(host,element[@"children"],locals)){NSDictionary *node=entry[@"element"],*scope=entry[@"locals"];if([node[@"kind"] isEqual:@"TabAccessory"]){if(BNPropBool(host,node,@"shown",scope,YES))[accessories addObject:entry];continue;}if(![node[@"kind"] isEqual:@"Tab"])continue;[entries addObject:entry];id choice=[host prop:node name:@"value" locals:scope];[choices addObject:choice?:BNNull()];NSUInteger variant=[BNDict(choice)[@"variant"] unsignedIntegerValue];[names addObject:BNString(BNDict(BNAt(BNArray(definition[@"variants"]),variant))[@"name"])];}
    NSUInteger selected=[choices indexOfObject:current];if(selected==NSNotFound&&choices.count){id fallback=[host prop:element name:@"fallback" locals:locals];selected=[choices indexOfObject:fallback];if(selected==NSNotFound)selected=0;[host setField:view.field value:choices[selected] locals:locals];}view.choices=choices;view.updating=YES;
#if TARGET_OS_OSX
    while(view.numberOfTabViewItems)[view removeTabViewItem:[view tabViewItemAtIndex:0]];
#else
    UITabBarController *tabs=(UITabBarController *)view.controller;NSMutableArray *controllers=[NSMutableArray array];
#endif
    for(NSUInteger index=0;index<entries.count;index++){NSDictionary *node=entries[index][@"element"],*scope=entries[index][@"locals"];NSString *label=BNPropString(host,node,@"label",scope),*icon=BNPropString(host,node,@"icon",scope);BOOL iconOnly=[BNPropString(host,node,@"display",scope) isEqual:@"icon"];BNLayout *page=BNContainer(@"column",8);page.fillWidth=YES;page.fillHeight=YES;
        if(index==selected){for(BNView *child in BNRendered(host,node[@"children"],scope))[page addSubview:child];for(NSDictionary *accessory in accessories)for(BNView *child in BNRendered(host,accessory[@"element"][@"children"],accessory[@"locals"]))[page addSubview:child];}
#if TARGET_OS_OSX
        NSTabViewItem *item=[[NSTabViewItem alloc]initWithIdentifier:names[index]];item.label=iconOnly&&icon.length?@"":label;if(icon.length)item.image=[NSImage imageWithSystemSymbolName:icon accessibilityDescription:label];item.view=page;[view addTabViewItem:item];
#else
        BNNativePageController *controller=[BNNativePageController new];[controller setPage:page];controller.tabBarItem=[[UITabBarItem alloc]initWithTitle:iconOnly?nil:label image:icon.length?[UIImage systemImageNamed:icon]:nil tag:(NSInteger)index];controller.tabBarItem.accessibilityLabel=label;[controllers addObject:controller];
#endif
        BNControl *entry=[host registerControl:node view:view role:@"tab" label:label locals:scope];__weak BNHost *weakHost=host;NSDictionary *field=view.field;id choice=choices[index];entry.activate=^{[weakHost setField:field value:choice locals:scope];};
    }
#if TARGET_OS_OSX
    if(selected<entries.count)[view selectTabViewItemAtIndex:selected];view.needsLayout=YES;
#else
    [tabs setViewControllers:controllers animated:NO];if(selected<controllers.count)tabs.selectedIndex=selected;tabs.tabBar.tintColor=host.accentColor;
#endif
    view.updating=NO;BNControl *control=[host registerControl:element view:view role:@"tabs" label:BNPropString(host,element,@"label",locals) locals:locals];__weak BNHost *weakHost=host;NSDictionary *field=view.field;control.select=^BOOL(NSString *name){NSUInteger index=[names indexOfObject:name];if(index==NSNotFound)return NO;return [weakHost setField:field value:choices[index] locals:locals];};BNContainerFill(view);return view;
}
