// Versioned subscriptions retain logical navigation/tab ownership until removal.
static NSSet<NSString *> *BNMediaLogicalQueryKeys(void);
@interface BNQuery : NSObject
@property(nonatomic,weak) BNHost *host;
@property(nonatomic,strong) BNWindow *window;
@property(nonatomic,strong) NSString *key;
@property(nonatomic,strong) NSDictionary *binding;
@property(nonatomic,strong) NSDictionary *locals;
@property(nonatomic,strong) NSData *wanted;
@property(nonatomic,strong) NSData *requested;
@property(nonatomic) uint64_t subscription;
@property(nonatomic) uint64_t version;
@property(nonatomic) uint8_t phase;
@property(nonatomic,strong) id data;
@property(nonatomic,strong) NSString *errorCode;
@property(nonatomic,strong) NSString *errorMessage;
@property(nonatomic) BOOL active;
@property(nonatomic) BOOL mounted;
@property(nonatomic) BOOL scheduled;
-(void)request;
-(void)receive:(NSData *)data;
-(void)close;
-(NSString *)summary;
@end

@interface BNHost (Queries)
-(NSMutableDictionary<NSString *,BNQuery *> *)nativeQueries;
-(void)beginQueries;
-(void)endQueries;
-(void)clearQueries;
-(void)receiveQuery:(uint64_t)subscription data:(NSData *)data;
-(BNView *)renderQuery:(NSDictionary *)element locals:(NSDictionary *)locals;
@end

@implementation BNQuery
-(void)close {
    if(_subscription && _host.handle) bern_query_close(_host.handle,_subscription);
    _subscription=0;
    _active=NO;
}
-(void)request {
    if(!_active || !_host.handle || !_window.generation) return;
    @try {
        if(!_subscription) {
            BNReader *opened=[[BNReader alloc] initWithData:BNTake(bern_query_open(_host.handle,(uint32_t)_window.kind,_window.generation,[_binding[@"query"] unsignedIntValue]))];
            if([opened u8]!=0) { NSString *code=[opened text], *message=[opened text]; BNThrow(code,message); }
            _subscription=[opened u64];
        }
        _requested=[_wanted copy];
        NSData *answer=BNTake(bern_query_request(_host.handle,_subscription,_requested.bytes,_requested.length));
        BNReader *reply=[[BNReader alloc] initWithData:answer];
        if([reply u8]!=0) { NSString *code=[reply text], *message=[reply text]; BNThrow(code,message); }
        [self receive:[answer subdataWithRange:NSMakeRange(1,answer.length-1)]];
    } @catch(NSException *problem) {
        _phase=4; _errorCode=problem.name; _errorMessage=problem.reason;
        [_host scheduleRender];
    }
}
-(void)receive:(NSData *)data {
    @try {
        BNReader *reader=[[BNReader alloc] initWithData:data];
        uint64_t version=[reader u64];
        if(version<_version || !_active) return;
        uint8_t phase=[reader u8];
        id value=_data;
        if(phase==2 || phase==3) value=[_host decode:_binding[@"result"] reader:reader];
        else if(phase==4) {
            value=[reader u8]==1 ? [_host decode:_binding[@"result"] reader:reader] : nil;
            _errorCode=[reader text]; _errorMessage=[reader text];
        } else if(phase>4) BNThrow(@"invalid_state",@"Unknown query phase");
        if(reader.position!=data.length) BNThrow(@"invalid_state",@"Trailing query state bytes");
        _version=version; _phase=phase; _data=value;
    } @catch(NSException *problem) {
        _phase=4; _errorCode=@"invalid_state"; _errorMessage=problem.reason;
    }
    [_host scheduleRender];
}
-(NSString *)summary {
    NSString *count=[_data isKindOfClass:[NSArray class]] ? [NSString stringWithFormat:@" (%lu)",(unsigned long)[_data count]] : @"";
    if(_phase==0) return @"idle";
    if(_phase==1 && BNIsNull(_data)) return [NSString stringWithFormat:@"loading v%llu",(unsigned long long)_version];
    if(_phase==4) return [NSString stringWithFormat:@"failed v%llu %@: %@%@",(unsigned long long)_version,_errorCode?:@"",_errorMessage?:@"",count];
    return [NSString stringWithFormat:@"%@ v%llu%@",_phase==2?@"ready":@"refreshing",(unsigned long long)_version,count];
}
@end

static NSString *BNQueryText(BNHost *host, NSString *key, NSString *fallback) {
    for(NSDictionary *text in host.model[@"texts"]) if([text[@"key"] isEqual:key]) {
        NSDictionary *translations=text[@"translations"];
        return translations[host.language] ?: translations[host.model[@"languages"][@"default"]] ?: fallback;
    }
    return fallback;
}

static BNView *BNQueryLabel(NSString *text) {
#if TARGET_OS_OSX
    NSTextField *label=[NSTextField wrappingLabelWithString:text];
    label.font=[NSFont systemFontOfSize:[NSFont systemFontSize]];
#else
    UILabel *label=[UILabel new]; label.text=text; label.numberOfLines=0;
    label.font=[UIFont preferredFontForTextStyle:UIFontTextStyleBody]; label.adjustsFontForContentSizeCategory=YES;
#endif
    return label;
}

@implementation BNHost (Queries)
-(NSMutableDictionary<NSString *,BNQuery *> *)nativeQueries {
    NSMutableDictionary *queries=objc_getAssociatedObject(self,@selector(nativeQueries));
    if(!queries) { queries=[NSMutableDictionary dictionary]; objc_setAssociatedObject(self,@selector(nativeQueries),queries,OBJC_ASSOCIATION_RETAIN_NONATOMIC); }
    return queries;
}
-(void)beginQueries { for(BNQuery *query in self.nativeQueries.allValues) query.mounted=NO; }
-(void)endQueries {
    NSSet *logical=BNMediaLogicalQueryKeys();
    for(NSString *key in [self.nativeQueries.allKeys copy]) {
        BNQuery *query=self.nativeQueries[key];
        if(!query.mounted && ![logical containsObject:key]) { [query close]; [self.nativeQueries removeObjectForKey:key]; }
        else if(!query.mounted) {
            BNWriter *writer=[BNWriter new];
            for(NSDictionary *arg in query.binding[@"args"]) [self encode:[self expr:arg locals:query.locals] type:arg[@"type"] writer:writer];
            query.wanted=writer.data;
            if(![query.wanted isEqual:query.requested] && !query.scheduled) { query.scheduled=YES; dispatch_async(dispatch_get_main_queue(), ^{ query.scheduled=NO; if(![query.wanted isEqual:query.requested]) [query request]; }); }
        }
    }
}
-(void)clearQueries { for(BNQuery *query in self.nativeQueries.allValues) [query close]; [self.nativeQueries removeAllObjects]; }
-(void)receiveQuery:(uint64_t)subscription data:(NSData *)data {
    for(BNQuery *query in self.nativeQueries.allValues) if(query.subscription==subscription) { [query receive:data]; return; }
}
-(BNView *)renderQuery:(NSDictionary *)element locals:(NSDictionary *)locals {
    BNWindow *window=locals[@"__window"];
    NSString *key=[NSString stringWithFormat:@"%@#%llu:%@:%@%@",window.identifier,(unsigned long long)window.generation,locals[@"__component"]?:@"",element[@"path"],locals[@"__keys"]?:@""];
    BNQuery *query=self.nativeQueries[key];
    NSDictionary *binding=element[@"props"][@"query"][@"query"];
    if(!query) { query=[BNQuery new]; query.host=self; query.window=window; query.key=key; query.binding=binding; self.nativeQueries[key]=query; }
    query.active=YES; query.mounted=YES; query.locals=locals;
    BNWriter *writer=[BNWriter new];
    for(NSDictionary *arg in binding[@"args"]) [self encode:[self expr:arg locals:locals] type:arg[@"type"] writer:writer];
    query.wanted=writer.data;
    if(![query.wanted isEqual:query.requested] && !query.scheduled) {
        query.scheduled=YES;
        dispatch_async(dispatch_get_main_queue(), ^{ query.scheduled=NO; if(![query.wanted isEqual:query.requested]) [query request]; });
    }
    BNLayout *layout=[BNLayout new]; layout.axis=@"vertical"; layout.gap=8; layout.fillWidth=YES;
    BNControl *control=[self registerControl:element view:layout role:@"query" label:@"" locals:locals];
    __weak BNQuery *weakQuery=query;
    control.activate=^{ [weakQuery request]; };
    control.value=^NSString *{ return [weakQuery summary]?:@"idle"; };
    id loading=[self prop:element name:@"loading" locals:locals];
    if(BNIsNull(loading)) loading=BNQueryText(self,@"bern.query.loading",@"Loading…");
    if(query.phase==0 || (query.phase==1 && BNIsNull(query.data))) {
#if TARGET_OS_OSX
        NSProgressIndicator *progress=[NSProgressIndicator new]; progress.style=NSProgressIndicatorStyleSpinning; [progress startAnimation:nil];
#else
        UIActivityIndicatorView *progress=[[UIActivityIndicatorView alloc] initWithActivityIndicatorStyle:UIActivityIndicatorViewStyleMedium]; [progress startAnimating];
#endif
        [layout addSubview:progress]; [layout addSubview:BNQueryLabel(BNString(loading))]; return layout;
    }
    if(query.phase==4) {
        id failed=[self prop:element name:@"failed" locals:locals];
        if(BNIsNull(failed)) failed=BNQueryText(self,@"bern.query.failed",@"Couldn’t Load");
        [layout addSubview:BNQueryLabel(BNString(failed))];
        [layout addSubview:BNQueryLabel(query.errorMessage?:@"")];
        NSString *retry=BNQueryText(self,@"bern.query.retry",@"Try Again");
#if TARGET_OS_OSX
        NSButton *button=[NSButton buttonWithTitle:retry target:control action:@selector(clicked:)];
#else
        UIButton *button=[UIButton buttonWithType:UIButtonTypeSystem]; [button setTitle:retry forState:UIControlStateNormal]; [button addTarget:control action:@selector(clicked:) forControlEvents:UIControlEventTouchUpInside];
#endif
        [layout addSubview:button];
    }
    if(!BNIsNull(query.data)) {
        id empty=[self prop:element name:@"empty" locals:locals];
        BOOL noData=[query.data isKindOfClass:[NSArray class]] && [query.data count]==0 && !BNIsNull(empty);
        if(noData) [layout addSubview:BNQueryLabel(BNString(empty))];
        else {
            NSMutableDictionary *inner=[locals mutableCopy];
            NSString *variable=element[@"template"][@"var"];
            if(variable) inner[variable]=query.data;
            for(BNView *view in [self nodes:element[@"children"] locals:inner]) [layout addSubview:view];
        }
    } else if(query.phase==2) {
        id empty=[self prop:element name:@"empty" locals:locals];
        if(!BNIsNull(empty)) [layout addSubview:BNQueryLabel(BNString(empty))];
    }
    if(query.phase==3 || (query.phase==1 && !BNIsNull(query.data))) {
#if TARGET_OS_OSX
        NSProgressIndicator *progress=[NSProgressIndicator new]; progress.style=NSProgressIndicatorStyleSpinning; [progress startAnimation:nil];
#else
        UIActivityIndicatorView *progress=[[UIActivityIndicatorView alloc] initWithActivityIndicatorStyle:UIActivityIndicatorViewStyleMedium]; [progress startAnimating];
#endif
        progress.accessibilityLabel=BNString(loading); [layout addSubview:progress];
    }
    return layout;
}
@end
