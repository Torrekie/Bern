#import <UniformTypeIdentifiers/UniformTypeIdentifiers.h>

static NSMutableDictionary<NSString *,NSURL *> *BNScopedFiles;
static NSMutableArray<NSURL *> *BNWaitingFiles;
static NSArray<NSString *> *BNFileWords(NSString *kinds) {
    NSArray *words=[kinds componentsSeparatedByCharactersInSet:[NSCharacterSet whitespaceAndNewlineCharacterSet]];
    NSMutableArray *result=[NSMutableArray array]; for(NSString *word in words) if(word.length) [result addObject:word];
    return result.count?result:@[@"any"];
}
static NSArray<UTType *> *BNFileTypes(BNHost *host, NSString *kinds) {
    NSDictionary *categories=@{@"any":@[UTTypeItem],@"video":@[UTTypeMovie,UTTypeVideo],@"audio":@[UTTypeAudio],@"picture":@[UTTypeImage],@"folder":@[UTTypeFolder]};
    NSMutableArray *types=[NSMutableArray array];
    for(NSString *word in BNFileWords(kinds)) {
        for(UTType *type in categories[word]) if(![types containsObject:type]) [types addObject:type];
        NSArray *extensions=[word hasPrefix:@"."]?@[[word substringFromIndex:1]]:host.model[@"file_kinds"][word];
        for(NSString *extension in extensions) { UTType *type=[UTType typeWithFilenameExtension:extension]; if(type && ![types containsObject:type]) [types addObject:type]; }
    }
    return types;
}
static BOOL BNFileAccepts(BNHost *host, NSURL *url, NSString *kinds) {
    if(!url || ![@[@"file",@"http",@"https"] containsObject:url.scheme.lowercaseString]) return NO;
    NSArray *words=BNFileWords(kinds); if([words containsObject:@"any"]) return YES;
    NSNumber *directory=nil; if(url.isFileURL) [url getResourceValue:&directory forKey:NSURLIsDirectoryKey error:nil];
    if(directory.boolValue) return [words containsObject:@"folder"];
    NSString *extension=url.pathExtension.lowercaseString; if(!extension.length) return NO;
    if([words containsObject:[@"." stringByAppendingString:extension]]) return YES;
    UTType *actual=[UTType typeWithFilenameExtension:extension];
    for(NSString *word in words) {
        if([host.model[@"file_kinds"][word] containsObject:extension]) return YES;
        if(![word isEqual:@"folder"]) for(UTType *wanted in BNFileTypes(host,word)) if([actual conformsToType:wanted]) return YES;
    }
    return NO;
}
static void BNRememberURL(NSURL *url) {
    if(!url.isFileURL) return;
    if(!BNScopedFiles) BNScopedFiles=[NSMutableDictionary dictionary];
    if(!BNScopedFiles[url.absoluteString] && [url startAccessingSecurityScopedResource]) BNScopedFiles[url.absoluteString]=url;
}
static void BNFilesStop(void) {
    for(NSURL *url in BNScopedFiles.allValues) [url stopAccessingSecurityScopedResource];
    [BNScopedFiles removeAllObjects]; [BNWaitingFiles removeAllObjects];
}
static void BNFilesDeliver(BNHost *host) {
    if(!BNWaitingFiles.count) return;
    NSArray *pending=[BNWaitingFiles copy]; [BNWaitingFiles removeAllObjects];
    for(NSURL *url in pending) {
        BOOL hasOpener=NO,delivered=NO;
        for(BNControl *control in [host.controls copy]) {
            if(![control.role isEqual:@"drop"] || !BNPropBool(host,control.element,@"opens",control.locals,NO)) continue;
            hasOpener=YES;
            if(control.enabled && control.setFile && BNFileAccepts(host,url,BNPropString(host,control.element,@"files",control.locals))) {
                [host performControl:control event:@"set_file" value:url.absoluteString]; delivered=YES; break;
            }
        }
        if(!delivered && !hasOpener) [BNWaitingFiles addObject:url];
    }
}
static void BNFilesOpenURLs(BNHost *host, NSArray<NSURL *> *urls) {
    if(!BNWaitingFiles) BNWaitingFiles=[NSMutableArray array];
    [BNWaitingFiles addObjectsFromArray:urls];
    if(!host.windows[host.model[@"windows"][@"primary"]] && !host.externalHost) [host openWindow:host.model[@"windows"][@"primary"] external:NO];
    BNFilesDeliver(host);
}

@interface BNDropView : BNLayout
#if !TARGET_OS_OSX
<UIDropInteractionDelegate>
#endif
@property(nonatomic,weak) BNHost *host;
@property(nonatomic,strong) NSDictionary *element;
@property(nonatomic,strong) NSDictionary *locals;
@property(nonatomic,weak) BNControl *control;
@property(nonatomic) BOOL over;
@property(nonatomic) BOOL dragging;
@property(nonatomic) uint64_t validationGeneration;
@property(nonatomic,strong) NSMutableDictionary<NSValue *,id> *validatedURLs;
-(void)setDragOver:(BOOL)over;
-(void)beginDrag;
-(void)endDrag;
-(void)refreshDragContent;
-(void)giveURL:(NSURL *)url;
@end

@implementation BNDropView
-(void)dealloc { if(_dragging) [_host endInteraction]; }
-(instancetype)initWithFrame:(CGRect)frame {
    if((self=[super initWithFrame:frame])) {
        self.axis=@"column"; self.fillWidth=YES;
#if TARGET_OS_OSX
        [self registerForDraggedTypes:@[NSPasteboardTypeFileURL]];
#else
        [self addInteraction:[[UIDropInteraction alloc] initWithDelegate:self]];
#endif
    }
    return self;
}
-(void)setDragOver:(BOOL)over {
    if(_over==over) return; _over=over;
    NSDictionary *field=_element[@"props"][@"over"][@"field"];
    if(field && [_host setField:field value:@(over) locals:_locals]) [self refreshDragContent];
}
-(void)beginDrag { if(_dragging)return; _dragging=YES; _validationGeneration++; _validatedURLs=[NSMutableDictionary dictionary]; [_host beginInteraction]; }
-(void)endDrag { if(!_dragging)return; [self setDragOver:NO]; _dragging=NO; _validationGeneration++; [_validatedURLs removeAllObjects]; [_host endInteraction]; }
-(void)refreshDragContent {
    NSMutableArray *old=[NSMutableArray array];
    for(BNControl *control in _host.controls) {
        if(control.view==self)continue;
        for(BNView *parent=control.view.superview;parent;parent=parent.superview) if(parent==self) { [old addObject:control]; break; }
    }
    [_host.controls removeObjectsInArray:old];
    for(BNView *child in [self.subviews copy]) [child removeFromSuperview];
    for(BNView *child in [_host nodes:_element[@"children"] locals:_locals]) [self addSubview:child];
    [self arrange];
}
-(void)giveURL:(NSURL *)url {
    [self setDragOver:NO];
    if(!_host || !_control.enabled || !BNFileAccepts(_host,url,BNPropString(_host,_element,@"files",_locals))) return;
    BNRememberURL(url);
    [_host performControl:_control event:@"set_file" value:url.absoluteString];
}
#if TARGET_OS_OSX
-(NSURL *)acceptedURL:(id<NSDraggingInfo>)sender {
    NSArray *urls=[sender.draggingPasteboard readObjectsForClasses:@[NSURL.class] options:@{NSPasteboardURLReadingFileURLsOnlyKey:@YES}];
    for(NSURL *url in urls) if(BNFileAccepts(_host,url,BNPropString(_host,_element,@"files",_locals))) return url;
    return nil;
}
-(NSDragOperation)draggingEntered:(id<NSDraggingInfo>)sender { [self beginDrag]; BOOL accepted=_control.enabled && [self acceptedURL:sender]!=nil; [self setDragOver:accepted]; return accepted?NSDragOperationCopy:NSDragOperationNone; }
-(NSDragOperation)draggingUpdated:(id<NSDraggingInfo>)sender { return [self draggingEntered:sender]; }
-(void)draggingExited:(id<NSDraggingInfo>)sender { [self endDrag]; }
-(BOOL)prepareForDragOperation:(id<NSDraggingInfo>)sender { return _control.enabled && [self acceptedURL:sender]!=nil; }
-(BOOL)performDragOperation:(id<NSDraggingInfo>)sender { NSURL *url=[self acceptedURL:sender]; if(!url) { [self endDrag]; return NO; } [self giveURL:url]; [self endDrag]; return YES; }
-(void)concludeDragOperation:(id<NSDraggingInfo>)sender { [self endDrag]; }
#else
-(NSArray<NSString *> *)acceptedIdentifiers {
    NSMutableArray *ids=[NSMutableArray arrayWithObject:UTTypeFileURL.identifier];
    for(UTType *type in BNFileTypes(_host,BNPropString(_host,_element,@"files",_locals))) [ids addObject:type.identifier];
    return ids;
}
-(BOOL)dropInteraction:(UIDropInteraction *)interaction canHandleSession:(id<UIDropSession>)session { return _control.enabled && [session hasItemsConformingToTypeIdentifiers:self.acceptedIdentifiers]; }
-(void)dropInteraction:(UIDropInteraction *)interaction sessionDidEnter:(id<UIDropSession>)session { [self beginDrag]; }
-(BOOL)acceptsSession:(id<UIDropSession>)session {
    if(!_control.enabled)return NO;
    NSString *kinds=BNPropString(_host,_element,@"files",_locals);
    if([BNFileWords(kinds) containsObject:@"any"])return YES;
    BOOL accepted=NO;
    for(UIDragItem *item in session.items) {
        NSItemProvider *provider=item.itemProvider;
        if([provider canLoadObjectOfClass:NSURL.class]) {
            NSValue *key=[NSValue valueWithNonretainedObject:provider]; id checked=_validatedURLs[key];
            if([checked isKindOfClass:NSURL.class]) { accepted=YES; continue; }
            if(checked)continue;
            _validatedURLs[key]=BNNull(); uint64_t generation=_validationGeneration; __weak BNDropView *weakSelf=self;
            [provider loadObjectOfClass:NSURL.class completionHandler:^(__kindof id<NSItemProviderReading> value,NSError *error) {
                dispatch_async(dispatch_get_main_queue(), ^{
                    BNDropView *strong=weakSelf; if(!strong || !strong.dragging || strong.validationGeneration!=generation)return;
                    BOOL valid=[value isKindOfClass:NSURL.class] && BNFileAccepts(strong.host,(NSURL *)value,kinds);
                    strong.validatedURLs[key]=valid?(NSURL *)value:@NO;
                    if(valid)[strong setDragOver:YES];
                });
            }];
        } else for(UTType *type in BNFileTypes(_host,kinds)) if([provider hasItemConformingToTypeIdentifier:type.identifier]) { accepted=YES; break; }
    }
    return accepted;
}
-(UIDropProposal *)dropInteraction:(UIDropInteraction *)interaction sessionDidUpdate:(id<UIDropSession>)session { [self beginDrag]; BOOL accepted=[self acceptsSession:session]; [self setDragOver:accepted]; return [[UIDropProposal alloc] initWithDropOperation:accepted?UIDropOperationCopy:UIDropOperationForbidden]; }
-(void)dropInteraction:(UIDropInteraction *)interaction sessionDidExit:(id<UIDropSession>)session { [self endDrag]; }
-(void)dropInteraction:(UIDropInteraction *)interaction sessionDidEnd:(id<UIDropSession>)session { [self endDrag]; }
-(void)dropInteraction:(UIDropInteraction *)interaction performDrop:(id<UIDropSession>)session {
    if(!_control.enabled) { [self endDrag]; return; }
    for(id validated in _validatedURLs.allValues) if([validated isKindOfClass:NSURL.class]) { [self giveURL:validated]; [self endDrag]; return; }
    [self endDrag];
    __weak BNDropView *weakSelf=self;
    for(UIDragItem *item in session.items) {
        NSItemProvider *provider=item.itemProvider;
        if([provider canLoadObjectOfClass:NSURL.class]) {
            [provider loadObjectOfClass:NSURL.class completionHandler:^(__kindof id<NSItemProviderReading> value,NSError *error) {
                if([value isKindOfClass:NSURL.class]) dispatch_async(dispatch_get_main_queue(), ^{ [weakSelf giveURL:(NSURL *)value]; });
            }];
            return;
        }
        for(NSString *type in self.acceptedIdentifiers) if([provider hasItemConformingToTypeIdentifier:type]) {
            [provider loadInPlaceFileRepresentationForTypeIdentifier:type completionHandler:^(NSURL *url,BOOL inPlace,NSError *error) {
                if(!url) return;
                // Providers may vend a temporary file valid only during this callback.
                // Copy that case into the app cache before crossing the queue boundary.
                NSURL *delivered=url;
                if(!inPlace) {
                    NSURL *cache=[[NSFileManager defaultManager] URLsForDirectory:NSCachesDirectory inDomains:NSUserDomainMask].firstObject;
                    NSURL *directory=[cache URLByAppendingPathComponent:@"BernDrop" isDirectory:YES];
                    [[NSFileManager defaultManager] createDirectoryAtURL:directory withIntermediateDirectories:YES attributes:nil error:nil];
                    delivered=[directory URLByAppendingPathComponent:[NSString stringWithFormat:@"%@-%@",NSUUID.UUID.UUIDString,url.lastPathComponent]];
                    if(![[NSFileManager defaultManager] copyItemAtURL:url toURL:delivered error:nil]) return;
                }
                dispatch_async(dispatch_get_main_queue(), ^{ [weakSelf giveURL:delivered]; });
            }];
            return;
        }
    }
}
#endif
@end

static BNView *BNRenderDrop(BNHost *host, NSDictionary *element, NSDictionary *locals) {
    BNWindow *window=locals[@"__window"];
    NSMapTable *cache=objc_getAssociatedObject(window,@selector(setDragOver:));
    if(!cache) { cache=[NSMapTable strongToWeakObjectsMapTable]; objc_setAssociatedObject(window,@selector(setDragOver:),cache,OBJC_ASSOCIATION_RETAIN_NONATOMIC); }
    NSString *key=[NSString stringWithFormat:@"%@.%@%@",locals[@"__component"]?:@"",element[@"path"],locals[@"__keys"]?:@""];
    BNDropView *view=[cache objectForKey:key]; if(!view) { view=[[BNDropView alloc] initWithFrame:CGRectZero]; [cache setObject:view forKey:key]; }
    view.host=host; view.element=element; view.locals=locals;
    for(BNView *child in [view.subviews copy]) [child removeFromSuperview];
    for(BNView *child in [host nodes:element[@"children"] locals:locals]) [view addSubview:child];
    BNControl *control=[host registerControl:element view:view role:@"drop" label:BNPropString(host,element,@"label",locals) locals:locals]; view.control=control;
    NSDictionary *field=element[@"props"][@"value"][@"field"];
    __weak BNHost *weakHost=host;
    control.setFile=^(NSURL *url) {
        BNHost *owner=weakHost; if(!owner) return;
        if(!BNFileAccepts(owner,url,BNPropString(owner,element,@"files",locals))) BNThrow(@"invalid_file_kind",@"This control does not accept that file type");
        BNRememberURL(url);
        if([owner setField:field value:@[url.absoluteString] locals:locals]) [owner action:element[@"action"] locals:locals];
    };
    control.value=^NSString *{ id source=[weakHost field:field locals:locals]; return BNIsNull(source)?@"":[BNAt(BNArray(source),0) description]; };
    return view;
}

void BernNativeOpenURL(NSURL *url) { BNFilesOpenURLs([BNHost shared],@[url]); }
