// Bern's native renderer. Both Objective-C and SwiftUI hosts use this file.
// All geometry is measured in points. No SwiftUI layout or SDK-new styling
// participates, so a host-language switch cannot change the rendered tree.
#import <UniformTypeIdentifiers/UniformTypeIdentifiers.h>
static NSArray<UTType *> *BNFileTypes(BNHost *host, NSString *kinds);

static const void *BNMetadataKey = &BNMetadataKey;
static const void *BNRetainedKey = &BNRetainedKey;
static const void *BNSidebarShownKey = &BNSidebarShownKey;
static const void *BNHoverTrackingKey = &BNHoverTrackingKey;
static void BNMotionReveal(BNView *view, BOOL shown);
static NSDictionary *BNMeta(BNView *view) { return BNDict(objc_getAssociatedObject(view, BNMetadataKey)); }
static void BNSetMeta(BNView *view, NSDictionary *metadata) { objc_setAssociatedObject(view, BNMetadataKey, metadata, OBJC_ASSOCIATION_RETAIN_NONATOMIC); }
static void BNKeep(BNView *view, id object) { objc_setAssociatedObject(view, BNRetainedKey, object, OBJC_ASSOCIATION_RETAIN_NONATOMIC); }
static CGFloat BNFinite(CGFloat value) { return isfinite(value) && value > 0 ? value : 0; }
static CGFloat BNPropNumber(BNHost *host, NSDictionary *element, NSString *name, NSDictionary *locals, CGFloat fallback) {
    id value = [host prop:element name:name locals:locals];
    return !BNIsNull(value) && [value respondsToSelector:@selector(doubleValue)] ? [value doubleValue] : fallback;
}
static NSString *BNPropString(BNHost *host, NSDictionary *element, NSString *name, NSDictionary *locals) { return BNString([host prop:element name:name locals:locals]); }
static BOOL BNPropBool(BNHost *host, NSDictionary *element, NSString *name, NSDictionary *locals, BOOL fallback) {
    id value = [host prop:element name:name locals:locals];
    if(BNIsNull(value)) return fallback;
    if([value isKindOfClass:NSString.class]) return [value isEqual:@"true"] || [value isEqual:@"yes"];
    return [value respondsToSelector:@selector(boolValue)] ? [value boolValue] : fallback;
}
static void BNNeedsLayout(BNView *view) {
#if TARGET_OS_OSX
    view.needsLayout = YES;
#else
    [view setNeedsLayout];
#endif
}
static void BNDecorations(BNView *view) {
    NSDictionary *indicator=BNDict(BNMeta(view)[@"styleIndicator"]);CALayer *found=nil;for(CALayer *layer in view.layer.sublayers)if([layer.name isEqual:@"bern.indicator"]){found=layer;break;}
    if(!indicator.count){[found removeFromSuperlayer];return;}if(!found){found=[CALayer layer];found.name=@"bern.indicator";[view.layer addSublayer:found];}
    NSString *edge=BNString(indicator[@"edge"]);CGFloat width=[indicator[@"width"] doubleValue];CGRect rect=view.bounds;
    if([edge isEqual:@"top"] || [edge isEqual:@"bottom"]){rect.size.height=width;if([edge isEqual:@"bottom"])rect.origin.y=view.bounds.size.height-width;}
    else{rect.size.width=width;if([edge isEqual:@"trailing"])rect.origin.x=view.bounds.size.width-width;}
    found.frame=rect;found.backgroundColor=(__bridge CGColorRef)indicator[@"color"];
}
static CALayer *BNLayer(BNView *view) {
#if TARGET_OS_OSX
    view.wantsLayer = YES;
#endif
    return view.layer;
}
static BOOL BNDark(BNView *view) {
#if TARGET_OS_OSX
    return [[view.effectiveAppearance bestMatchFromAppearancesWithNames:@[NSAppearanceNameAqua, NSAppearanceNameDarkAqua]] isEqual:NSAppearanceNameDarkAqua];
#else
    return view.traitCollection.userInterfaceStyle == UIUserInterfaceStyleDark;
#endif
}
static BNColor *BNRole(NSString *role) {
#if TARGET_OS_OSX
    if([role isEqual:@"surface.canvas"]) return NSColor.windowBackgroundColor;
    if([role isEqual:@"surface.panel"]) return NSColor.controlBackgroundColor;
    if([role isEqual:@"surface.raised"]) return NSColor.textBackgroundColor;
    if([role isEqual:@"text.secondary"] || [role isEqual:@"icon.secondary"]) return NSColor.secondaryLabelColor;
    if([role isEqual:@"text.placeholder"] || [role isEqual:@"disabled.foreground"]) return NSColor.tertiaryLabelColor;
    if([role isEqual:@"accent"] || [role isEqual:@"focus.indicator"]) return [BNHost shared].accentColor ?: NSColor.controlAccentColor;
    if([role isEqual:@"on_accent"] || [role isEqual:@"selection.foreground"]) return NSColor.alternateSelectedControlTextColor;
    if([role isEqual:@"selection.background"]) return [([BNHost shared].accentColor ?: NSColor.controlAccentColor) colorWithAlphaComponent:0.18];
    if([role isEqual:@"control.border"]) return NSColor.separatorColor;
    if([role isEqual:@"control.track"] || [role isEqual:@"disabled.surface"]) return NSColor.quaternaryLabelColor;
    if([role isEqual:@"control.thumb"]) return NSColor.whiteColor;
    if([role isEqual:@"status.success"]) return NSColor.systemGreenColor;
    if([role isEqual:@"status.warning"]) return NSColor.systemOrangeColor;
    if([role isEqual:@"status.error"]) return NSColor.systemRedColor;
    if([role isEqual:@"fill.subtle"]) return [NSColor.labelColor colorWithAlphaComponent:0.06];
    if([role isEqual:@"fill.strong"]) return [NSColor.labelColor colorWithAlphaComponent:0.16];
    return NSColor.labelColor;
#else
    if([role isEqual:@"surface.canvas"]) return UIColor.systemBackgroundColor;
    if([role isEqual:@"surface.panel"]) return UIColor.secondarySystemBackgroundColor;
    if([role isEqual:@"surface.raised"]) return UIColor.tertiarySystemBackgroundColor;
    if([role isEqual:@"text.secondary"] || [role isEqual:@"icon.secondary"]) return UIColor.secondaryLabelColor;
    if([role isEqual:@"text.placeholder"] || [role isEqual:@"disabled.foreground"]) return UIColor.placeholderTextColor;
    if([role isEqual:@"accent"] || [role isEqual:@"focus.indicator"]) return [BNHost shared].accentColor ?: UIColor.systemBlueColor;
    if([role isEqual:@"on_accent"] || [role isEqual:@"selection.foreground"]) return UIColor.whiteColor;
    if([role isEqual:@"selection.background"]) return [([BNHost shared].accentColor ?: UIColor.systemBlueColor) colorWithAlphaComponent:0.18];
    if([role isEqual:@"control.border"]) return UIColor.separatorColor;
    if([role isEqual:@"control.track"] || [role isEqual:@"disabled.surface"]) return UIColor.systemFillColor;
    if([role isEqual:@"control.thumb"]) return UIColor.whiteColor;
    if([role isEqual:@"status.success"]) return UIColor.systemGreenColor;
    if([role isEqual:@"status.warning"]) return UIColor.systemOrangeColor;
    if([role isEqual:@"status.error"]) return UIColor.systemRedColor;
    if([role isEqual:@"fill.subtle"]) return UIColor.quaternarySystemFillColor;
    if([role isEqual:@"fill.strong"]) return UIColor.secondarySystemFillColor;
    return UIColor.labelColor;
#endif
}
static BNColor *BNColorRef(id reference, BNView *view) {
    NSDictionary *ref = BNDict(reference);
    if([ref[@"kind"] isEqual:@"role"]) return BNRole(BNString(ref[@"role"]));
    NSDictionary *rgb = BNDict(ref[BNDark(view) ? @"dark" : @"light"]);
    if(!rgb.count) return BNRole(@"text.primary");
    CGFloat r=[rgb[@"red"] doubleValue]/255, g=[rgb[@"green"] doubleValue]/255, b=[rgb[@"blue"] doubleValue]/255;
#if TARGET_OS_OSX
    return [NSColor colorWithSRGBRed:r green:g blue:b alpha:1];
#else
    return [UIColor colorWithRed:r green:g blue:b alpha:1];
#endif
}
static BNFont *BNTextFont(BNHost *host, NSDictionary *element, NSDictionary *locals) {
    NSString *style = BNPropString(host, element, @"style", locals);
#if TARGET_OS_OSX
    NSDictionary *sizes=@{@"large_title":@26,@"title":@22,@"title2":@17,@"title3":@15,@"headline":@13,@"subheadline":@12,@"body":@13,@"callout":@12,@"footnote":@10,@"caption":@10,@"caption2":@10,@"control":@13};
#else
    NSDictionary *sizes=@{@"large_title":@34,@"title":@28,@"title2":@22,@"title3":@20,@"headline":@17,@"subheadline":@15,@"body":@17,@"callout":@16,@"footnote":@13,@"caption":@12,@"caption2":@11,@"control":@17};
#endif
    CGFloat size=BNPropNumber(host,element,@"font_size",locals,[sizes[style.length ? style : @"body"] doubleValue]);
    CGFloat weight=[style isEqual:@"headline"] ? 0.23 : 0;
    NSDictionary *weights=@{@"ultralight":@(-0.8),@"thin":@(-0.6),@"light":@(-0.4),@"regular":@0,@"medium":@0.23,@"semibold":@0.3,@"bold":@0.4,@"heavy":@0.56,@"black":@0.62};
    for(NSDictionary *entry in BNArray(BNDict(host.model[@"style"])[@"text_weights"])) {
        if([entry[@"style"] isEqual:style.length ? style : @"body"]) {
            if(BNIsNull(BNDict(element[@"props"])[@"font_size"]) && !BNIsNull(entry[@"size"])) size=[entry[@"size"] doubleValue];
            weight=[weights[entry[@"weight"]] doubleValue];
        }
    }
    return [BNFont systemFontOfSize:MAX(1,size) weight:weight];
}
static void BNAccessibility(BNView *view, NSString *identifier, NSString *label) {
#if TARGET_OS_OSX
    if(identifier.length && !view.accessibilityIdentifier.length) [view setAccessibilityIdentifier:identifier];
    if(label.length) [view setAccessibilityLabel:label];
#else
    if(identifier.length && !view.accessibilityIdentifier.length) view.accessibilityIdentifier=identifier;
    if(label.length) view.accessibilityLabel=label;
#endif
}
static BNView *BNLabel(BNHost *host, NSString *text, NSDictionary *element, NSDictionary *locals) {
#if TARGET_OS_OSX
    NSTextField *label=[NSTextField labelWithString:text ?: @""];
    label.font=BNTextFont(host,element,locals); label.textColor=BNRole(@"text.primary");
    label.maximumNumberOfLines=(NSInteger)BNPropNumber(host,element,@"lines",locals,0);
    label.lineBreakMode=NSLineBreakByTruncatingTail;
    label.selectable=YES;
#else
    UILabel *label=[[UILabel alloc] initWithFrame:CGRectZero]; label.text=text;
    label.font=BNTextFont(host,element,locals); label.textColor=BNRole(@"text.primary");
    label.numberOfLines=(NSInteger)BNPropNumber(host,element,@"lines",locals,0);
    label.adjustsFontForContentSizeCategory=YES;
#endif
    NSString *emphasis=BNPropString(host,element,@"emphasis",locals);
    if([emphasis isEqual:@"secondary"]) label.textColor=BNRole(@"text.secondary");
    if([emphasis isEqual:@"tertiary"]) label.textColor=BNRole(@"text.placeholder");
    NSString *mark=BNPropString(host,element,@"mark",locals);CGFloat lineHeight=BNPropNumber(host,element,@"line_height",locals,0);
    if(mark.length || lineHeight>0){NSMutableDictionary *attributes=[NSMutableDictionary dictionaryWithDictionary:@{NSFontAttributeName:label.font,NSForegroundColorAttributeName:label.textColor}];if(mark.length){attributes[NSUnderlineStyleAttributeName]=@(NSUnderlineStyleSingle);attributes[NSUnderlineColorAttributeName]=BNRole(mark);}if(lineHeight>0){NSMutableParagraphStyle *paragraph=[NSMutableParagraphStyle new];paragraph.minimumLineHeight=lineHeight;paragraph.maximumLineHeight=lineHeight;attributes[NSParagraphStyleAttributeName]=paragraph;}NSAttributedString *attributed=[[NSAttributedString alloc] initWithString:text ?: @"" attributes:attributes];
#if TARGET_OS_OSX
        label.attributedStringValue=attributed;
#else
        label.attributedText=attributed;
#endif
    }
    BNSetMeta(label,@{@"kind":@"Text",@"element":element,@"locals":locals});
    return label;
}

// Structural containers need descriptors before views exist. Preserve each
// branch's local scope while flattening conditions, components and repetitions.
static NSArray<NSDictionary *> *BNDescriptorsAt(BNHost *host, NSArray *nodes, NSDictionary *locals, NSUInteger depth) {
    if(depth>128)BNThrow(@"invalid_node",@"UI component expansion exceeds 128 levels");
    NSMutableArray *result=[NSMutableArray array];
    for(NSDictionary *raw in BNArray(nodes)){
        NSDictionary *node=BNDict(raw);NSString *tag=BNString(node[@"node"]);
        if([tag isEqual:@"component"]){for(NSDictionary *component in BNArray(host.model[@"components"]))if([component[@"name"] isEqual:node[@"component"]]){NSMutableDictionary *inner=[locals mutableCopy];inner[@"__component"]=component[@"name"];for(NSArray *argument in BNArray(node[@"args"]))if([argument[1][@"kind"] isEqual:@"value"])inner[argument[0]]=[host expr:argument[1][@"expr"] locals:locals] ?: BNNull();[result addObjectsFromArray:BNDescriptorsAt(host,@[component[@"body"]],inner,depth+1)];}continue;}
        if([tag isEqual:@"if"]){NSArray *body=BNArray(node[@"otherwise"]);for(NSArray *branch in BNArray(node[@"branches"]))if([[host expr:branch[0] locals:locals] boolValue]){body=BNArray(branch[1]);break;}[result addObjectsFromArray:BNDescriptorsAt(host,body,locals,depth+1)];continue;}
        if([tag isEqual:@"if_let"]){id value=[host expr:node[@"value"] locals:locals];NSMutableDictionary *inner=[locals mutableCopy];if(!BNIsNull(value))inner[node[@"var"]]=value;[result addObjectsFromArray:BNDescriptorsAt(host,BNArray(node[BNIsNull(value) ? @"otherwise" : @"then"]),inner,depth+1)];continue;}
        if([tag isEqual:@"match"]){id value=[host expr:node[@"value"] locals:locals];for(NSDictionary *arm in BNArray(node[@"arms"]))if(BNIsNull(arm[@"variant"]) || [arm[@"variant"] isEqual:BNDict(value)[@"variant"]]){NSMutableDictionary *inner=[locals mutableCopy];for(NSDictionary *binding in BNArray(arm[@"bindings"]))inner[binding[@"name"]]=BNAt(BNArray(BNDict(value)[@"fields"]),[binding[@"field"] unsignedIntegerValue]);[result addObjectsFromArray:BNDescriptorsAt(host,BNArray(arm[@"body"]),inner,depth+1)];break;}continue;}
        if([tag isEqual:@"fragment"]){[result addObjectsFromArray:BNDescriptorsAt(host,BNArray(node[@"children"]),locals,depth+1)];continue;}
        NSDictionary *element=BNDict(node[@"element"]).count ? node[@"element"] : node;
        if([element[@"kind"] isEqual:@"ForEach"]){NSArray *items=BNArray([host prop:element name:@"items" locals:locals]);NSDictionary *template=BNDict(element[@"template"]),*key=BNDict(BNDict(element[@"props"])[@"key"]);NSUInteger index=0;
            for(id item in items){NSMutableDictionary *inner=[locals mutableCopy];if(template[@"var"])inner[template[@"var"]]=item;id identity=key[@"field"] ? BNAt(BNArray(item),[key[@"field"] unsignedIntegerValue]) : @(index);inner[@"__itemKey"]=identity;inner[@"__keys"]=[NSString stringWithFormat:@"%@[%@]",locals[@"__keys"] ?: @"",BNString(identity)];[result addObjectsFromArray:BNDescriptorsAt(host,BNArray(element[@"children"]),inner,depth+1)];index++;}continue;
        }
        [result addObject:@{@"element":element,@"locals":locals}];
    }
    return result;
}
static NSArray<NSDictionary *> *BNDescriptors(BNHost *host, NSArray *nodes, NSDictionary *locals) {return BNDescriptorsAt(host,nodes,locals,0);}
static NSArray<BNView *> *BNRendered(BNHost *host, NSArray *nodes, NSDictionary *locals) {
    NSMutableArray *views=[NSMutableArray array];
    for(NSDictionary *descriptor in BNDescriptors(host,nodes,locals)){BNView *view=[host renderElement:descriptor[@"element"] locals:descriptor[@"locals"]];if(view)[views addObject:view];}
    return views;
}

static CGSize BNMeasure(BNView *view, CGSize available);
static void BNPlace(BNView *view, CGRect rect);
static BOOL BNGrows(BNView *view, BOOL horizontal) {
    NSDictionary *meta=BNMeta(view);NSString *axis=BNString(meta[@"growAxis"]);
    if([meta[@"kind"] isEqual:@"Spacer"])return YES;
    if([view isKindOfClass:BNLayout.class]){BNLayout *layout=(BNLayout *)view;if(horizontal ? layout.fillWidth : layout.fillHeight)return YES;}
    return [meta[@"grow"] boolValue] && (!axis.length || [axis isEqual:horizontal ? @"horizontal" : @"vertical"]);
}
static CGFloat BNFirstBaseline(BNView *view, CGSize size) {
    if([view respondsToSelector:@selector(font)]){BNFont *font=[(id)view font];if(font){
#if TARGET_OS_OSX
        CGFloat line=font.ascender-font.descender+font.leading;
#else
        CGFloat line=font.lineHeight;
#endif
        return MAX(0,(size.height-line)/2)+font.ascender;
    }}
    if([view isKindOfClass:BNLayout.class])for(BNView *child in view.subviews){CGSize childSize=BNMeasure(child,size);if([child respondsToSelector:@selector(font)])return BNFirstBaseline(child,childSize);}
    return size.height/2;
}
static BNLayout *BNContainer(NSString *axis, CGFloat gap) {
    BNLayout *view=[[BNLayout alloc] initWithFrame:CGRectZero]; view.axis=axis; view.gap=gap; view.alignment=@"leading";
    return view;
}
static NSDictionary *BNTextProperty(NSString *text) {return @{@"kind":@"text",@"text":@{@"kind":@"dynamic",@"expr":@{@"kind":@{@"kind":@"literal",@"value":@{@"text":text ?: @""}},@"type":@{@"kind":@"text"}}}};}

@implementation BNLayout
#if TARGET_OS_OSX
-(BOOL)isFlipped { return YES; }
-(NSView *)hitTest:(NSPoint)point {return [BNMeta(self)[@"revealHidden"] boolValue] || [BNMeta(self)[@"disabled"] boolValue] ? nil : [super hitTest:point];}
-(void)updateTrackingAreas {[super updateTrackingAreas];NSTrackingArea *previous=objc_getAssociatedObject(self,BNHoverTrackingKey);if(previous)[self removeTrackingArea:previous];NSTrackingArea *tracking=[[NSTrackingArea alloc] initWithRect:self.bounds options:NSTrackingMouseEnteredAndExited|NSTrackingActiveInKeyWindow|NSTrackingInVisibleRect owner:self userInfo:nil];[self addTrackingArea:tracking];objc_setAssociatedObject(self,BNHoverTrackingKey,tracking,OBJC_ASSOCIATION_RETAIN_NONATOMIC);}
-(void)mouseEntered:(NSEvent *)event {BNMotionReveal(self,YES);}
-(void)mouseExited:(NSEvent *)event {BNMotionReveal(self,NO);}
-(void)layout { [super layout]; [self arrange]; }
#else
-(UIView *)hitTest:(CGPoint)point withEvent:(UIEvent *)event {return [BNMeta(self)[@"revealHidden"] boolValue] || [BNMeta(self)[@"disabled"] boolValue] ? nil : [super hitTest:point withEvent:event];}
-(void)layoutSubviews { [super layoutSubviews]; [self arrange]; }
#endif
-(CGSize)intrinsicContentSize { return [self measure:CGSizeMake(100000,100000)]; }
-(CGSize)measure:(CGSize)available {
    CGFloat px=_paddingX+_padding, py=_paddingY+_padding;
    CGFloat width=_requestedWidth>0 ? _requestedWidth : BNFinite(available.width);
    CGFloat inside=MAX(0,width-2*px), w=0,h=0; NSUInteger count=self.subviews.count;
    NSDictionary *meta=BNMeta(self);
    if([_axis isEqual:@"grid"]) {
        CGFloat minimum=MAX(1,[meta[@"minimum"] doubleValue]), rowGap=meta[@"rowGap"] ? [meta[@"rowGap"] doubleValue] : _gap;
        NSUInteger columns=MAX((NSUInteger)1,(NSUInteger)floor((inside+_gap)/(minimum+_gap)));
        CGFloat cell=MAX(0,(inside-_gap*(columns-1))/columns), row=0;
        for(NSUInteger i=0;i<count;i++) {
            CGSize size=BNMeasure(self.subviews[i],CGSizeMake(cell,available.height));
            CGFloat ratio=[meta[@"ratio"] doubleValue]; row=MAX(row,ratio>0 ? cell/ratio+[meta[@"extra"] doubleValue] : size.height);
            if((i+1)%columns==0 || i+1==count) { h+=row; if(i+1<count) h+=rowGap; row=0; }
        }
        w=inside;
    } else if([_axis isEqual:@"flow"]) {
        CGFloat x=0,row=0;
        for(BNView *child in self.subviews) { CGSize size=BNMeasure(child,CGSizeMake(inside,available.height));
            if([BNMeta(child)[@"kind"] isEqual:@"Spacer"])size.width=MAX(0,inside-x-(x>0 ? _gap : 0));
            if(x>0 && x+size.width>inside) { h+=row+_gap; x=0; row=0; }
            x+=size.width+(x>0 ? _gap : 0); w=MAX(w,x); row=MAX(row,size.height);
        } h+=row;
    } else if([_axis isEqual:@"row"] || [_axis isEqual:@"split"]) {
        CGFloat above=0,below=0;for(BNView *child in self.subviews) { CGSize size=BNMeasure(child,CGSizeMake(inside,available.height)); w+=size.width; h=MAX(h,size.height);CGFloat baseline=BNFirstBaseline(child,size);above=MAX(above,baseline);below=MAX(below,size.height-baseline); }if([_alignment isEqual:@"baseline"])h=MAX(h,above+below);
        if(count>1) w+=_gap*(count-1);
        if([_axis isEqual:@"split"]) { w=inside; h=BNFinite(available.height); }
    } else if(_overlay || [_axis isEqual:@"stack"] || [_axis isEqual:@"rail"] || [_axis isEqual:@"positioned"] || [_axis isEqual:@"scale"]) {
        for(BNView *child in self.subviews) { CGSize size=BNMeasure(child,CGSizeMake(inside,available.height)); w=MAX(w,size.width); h=MAX(h,size.height); }
        if([_axis isEqual:@"rail"]) w=inside;
    } else if([_axis isEqual:@"accordion"]) {
        w=inside; h=[meta[@"height"] doubleValue];
    } else {
        for(BNView *child in self.subviews) { CGSize size=BNMeasure(child,CGSizeMake(inside,available.height)); w=MAX(w,size.width); h+=size.height; }
        if(count>1) h+=_gap*(count-1);
    }
    w+=px*2; h+=py*2;
    if(_requestedWidth>0) w=_requestedWidth; else if(_fillWidth && available.width<100000) w=available.width;
    if(_requestedHeight>0) h=_requestedHeight; else if(_fillHeight && available.height<100000) h=available.height;
    return CGSizeMake(MAX(0,w),MAX(0,h));
}
-(void)arrange {
    CGFloat px=_paddingX+_padding,py=_paddingY+_padding;
    CGFloat width=MAX(0,self.bounds.size.width-2*px),height=MAX(0,self.bounds.size.height-2*py);
    NSUInteger count=self.subviews.count; if(!count) return;
    NSDictionary *meta=BNMeta(self);
    if([_axis isEqual:@"grid"]) {
        CGFloat minimum=MAX(1,[meta[@"minimum"] doubleValue]),rowGap=meta[@"rowGap"] ? [meta[@"rowGap"] doubleValue] : _gap;
        NSUInteger columns=MAX((NSUInteger)1,(NSUInteger)floor((width+_gap)/(minimum+_gap)));
        CGFloat cell=MAX(0,(width-_gap*(columns-1))/columns),y=py;
        for(NSUInteger start=0;start<count;start+=columns) {
            CGFloat row=0,ratio=[meta[@"ratio"] doubleValue];
            for(NSUInteger i=start;i<MIN(start+columns,count);i++) { CGSize size=BNMeasure(self.subviews[i],CGSizeMake(cell,height)); row=MAX(row,ratio>0 ? cell/ratio+[meta[@"extra"] doubleValue] : size.height); }
            for(NSUInteger i=start;i<MIN(start+columns,count);i++) { BNView *child=self.subviews[i]; CGSize size=BNMeasure(child,CGSizeMake(cell,height)); BNPlace(child,CGRectMake(px+(i-start)*(cell+_gap),y,cell,size.height)); }
            y+=row+rowGap;
        } return;
    }
    if([_axis isEqual:@"flow"]) {
        CGFloat x=0,y=py,row=0; NSMutableArray *line=[NSMutableArray array];
        for(NSUInteger index=0;index<=count;index++) {
            BNView *child=index<count ? self.subviews[index] : nil; CGSize size=child ? BNMeasure(child,CGSizeMake(width,height)) : CGSizeZero;
            if(child && [BNMeta(child)[@"kind"] isEqual:@"Spacer"])size.width=MAX(0,width-x-(x>0 ? _gap : 0));
            if(!child || (x>0 && x+_gap+size.width>width)) {
                for(BNView *item in line) { CGRect r=item.frame;r.origin.y=y+(row-r.size.height)/2;BNPlace(item,r); }
                y+=row+_gap;x=0;row=0;[line removeAllObjects];
            }
            if(child) { if(x>0)x+=_gap; BNPlace(child,CGRectMake(px+x,y,MIN(width,size.width),size.height));[line addObject:child];x+=size.width;row=MAX(row,size.height); }
        } return;
    }
    if([_axis isEqual:@"split"]) {
        CGFloat sidebar=[meta[@"sidebar"] doubleValue]; if(sidebar<=0) sidebar=210;
        sidebar=MIN(sidebar,MAX(160,width*0.4));
        BOOL compact=width<600;
        BOOL showsSidebar=[meta[@"showSidebar"] boolValue];
        for(NSUInteger i=0;i<count;i++) {
            BNView *child=self.subviews[i]; BOOL shown=!compact || (showsSidebar ? i==0 : i>0); child.hidden=!shown;
            if(!shown) continue;
            CGRect rect=compact ? CGRectMake(px,py,width,height) : i==0 ? CGRectMake(px,py,sidebar,height) : CGRectMake(px+sidebar+1,py,MAX(0,width-sidebar-1),height);
            BNPlace(child,rect);
        } return;
    }
    if([_axis isEqual:@"accordion"]) {
        CGFloat available=MAX(0,width-_gap*(count-1)),collapsed=MIN(MAX(0,[meta[@"collapsed"] doubleValue]),available/count);NSUInteger selected=MIN(count-1,(NSUInteger)MAX(0,[meta[@"selected"] integerValue]));
        CGFloat open=MAX(0,available-collapsed*(count-1)),x=px;
        for(NSUInteger i=0;i<count;i++) { CGFloat w=i==selected ? open : collapsed;BNLayer(self.subviews[i]).masksToBounds=YES;BNLayer(self.subviews[i]).cornerRadius=[meta[@"corner"] doubleValue];BNPlace(self.subviews[i],CGRectMake(x,py,w,height));x+=w+_gap; }return;
    }
    if([_axis isEqual:@"rail"]) {
        BOOL vertical=[meta[@"vertical"] boolValue]; CGFloat overhang=[meta[@"overhang"] doubleValue],anchor=[meta[@"anchor"] doubleValue];
        for(BNView *child in self.subviews) { NSDictionary *m=BNMeta(child); CGSize size=BNMeasure(child,CGSizeMake(width,height));
            CGFloat length=(vertical ? height : width)+2*overhang,at=[m[@"at"] doubleValue];
            CGRect r=CGRectMake(px+(width-size.width)/2,py+(height-size.height)/2,size.width,size.height);
            if(m[@"from"] && m[@"to"]) { CGFloat start=[m[@"from"] doubleValue]*length-overhang,end=[m[@"to"] doubleValue]*length-overhang;
                if(vertical){r.origin.y=py+MIN(start,end);r.size.height=fabs(end-start);}else{r.origin.x=px+MIN(start,end);r.size.width=fabs(end-start);}
            } else if(vertical) r.origin.y=py+at*length-overhang-anchor*size.height; else r.origin.x=px+at*length-overhang-anchor*size.width;
            BNPlace(child,r);
        }return;
    }
    if([_axis isEqual:@"scale"]) {
        CGFloat designWidth=MAX(1,[meta[@"designWidth"] doubleValue]),designHeight=MAX(1,[meta[@"designHeight"] doubleValue]);
        CGFloat scale=MIN(width/designWidth,height/designHeight);
        CGFloat offsetX=(width-designWidth*scale)/2,offsetY=(height-designHeight*scale)/2;
        for(BNView *child in self.subviews) {NSMutableDictionary *childMeta=[BNMeta(child) mutableCopy];childMeta[@"sceneRoom"]=@{@"width":@(designWidth),@"height":@(designHeight),@"x":@(scale>0 ? offsetX/scale : 0),@"y":@(scale>0 ? offsetY/scale : 0)};BNSetMeta(child,childMeta);
#if TARGET_OS_OSX
            // AppKit's bounds transform scales drawing and hit testing together.
            // A layer-only transform would leave NSControl hit targets unscaled.
            BNLayer(child).transform=CATransform3DIdentity;child.frame=CGRectMake(px+offsetX,py+offsetY,designWidth*scale,designHeight*scale);child.bounds=CGRectMake(0,0,designWidth,designHeight);if([child isKindOfClass:BNLayout.class])[(BNLayout *)child arrange];
#else
            BNPlace(child,CGRectMake(0,0,designWidth,designHeight));CALayer *layer=BNLayer(child);layer.anchorPoint=CGPointZero;layer.position=CGPointMake(px+offsetX,py+offsetY);layer.transform=CATransform3DMakeScale(scale,scale,1);
#endif
        }return;
    }
    if(_overlay || [_axis isEqual:@"stack"] || [_axis isEqual:@"positioned"]) {
        for(BNView *child in self.subviews) { CGSize size=BNMeasure(child,CGSizeMake(width,height)); NSDictionary *m=BNMeta(child);
            BOOL fills=[m[@"fills"] boolValue]; if(fills) size=CGSizeMake(width,height);
            CGFloat x=px,y=py;
            if([_alignment containsString:@"trailing"])x+=width-size.width;else if(![_alignment containsString:@"leading"])x+=(width-size.width)/2;
            if([_alignment containsString:@"bottom"])y+=height-size.height;else if(![_alignment containsString:@"top"])y+=(height-size.height)/2;
            if([m[@"kind"] isEqual:@"Positioned"]) {x=px+[m[@"x"] doubleValue];y=py+[m[@"y"] doubleValue];NSDictionary *room=BNDict(meta[@"sceneRoom"]);if(room.count && BNPropBool([BNHost shared],BNDict(m[@"element"]),@"bleed",BNDict(m[@"locals"]),NO)){CGFloat left=x-px<=0.5 ? [room[@"x"] doubleValue] : 0,right=x-px+size.width>=[room[@"width"] doubleValue]-0.5 ? [room[@"x"] doubleValue] : 0,top=y-py<=0.5 ? [room[@"y"] doubleValue] : 0,bottom=y-py+size.height>=[room[@"height"] doubleValue]-0.5 ? [room[@"y"] doubleValue] : 0;x-=left;y-=top;size.width+=left+right;size.height+=top+bottom;}}
            BNPlace(child,CGRectMake(x,y,size.width,size.height));
        }return;
    }
    if([_axis isEqual:@"row"]) {
        NSMutableArray *sizes=[NSMutableArray array];CGFloat used=_gap*(count-1),grow=0,baseline=0;
        for(BNView *child in self.subviews) {CGSize s=BNMeasure(child,CGSizeMake(BNGrows(child,YES) ? 100000 : width,height));[sizes addObject:@[@(s.width),@(s.height)]];used+=s.width;if(BNGrows(child,YES))grow++;baseline=MAX(baseline,BNFirstBaseline(child,s));}
        CGFloat spare=MAX(0,width-used),shrink=used>width && used>_gap*(count-1) ? MAX(0,(width-_gap*(count-1))/(used-_gap*(count-1))) : 1,x=px;
        for(NSUInteger i=0;i<count;i++) {BNView *child=self.subviews[i];NSArray *s=sizes[i];CGFloat w=[s[0] doubleValue]*shrink,h=[s[1] doubleValue];if(BNGrows(child,YES) && grow>0)w+=spare/grow;
            CGFloat y=py+([_alignment isEqual:@"top"] ? 0 : [_alignment isEqual:@"bottom"] ? height-h : (height-h)/2);
            if([_alignment isEqual:@"baseline"])y=py+baseline-BNFirstBaseline(child,CGSizeMake(w,h));
            BNPlace(child,CGRectMake(x,y,MAX(0,w),h));x+=w+_gap;
        }return;
    }
    CGFloat y=py,total=0,grow=0;NSMutableArray *sizes=[NSMutableArray array];
    for(BNView *child in self.subviews) {CGSize s=BNMeasure(child,CGSizeMake(width,BNGrows(child,NO) ? 100000 : height));[sizes addObject:@[@(s.width),@(s.height)]];total+=s.height;if(BNGrows(child,NO))grow++;}
    total+=_gap*(count-1);CGFloat spare=MAX(0,height-total);
    for(NSUInteger i=0;i<count;i++) {BNView *child=self.subviews[i];NSArray *s=sizes[i];CGFloat w=[s[0] doubleValue],h=[s[1] doubleValue];
        if([BNMeta(child)[@"fillWidth"] boolValue] || ([child isKindOfClass:BNLayout.class] && ((BNLayout *)child).fillWidth))w=width;
        if(BNGrows(child,NO) && grow>0)h+=spare/grow;
        CGFloat x=px+([_alignment isEqual:@"center"] ? (width-w)/2 : [_alignment isEqual:@"trailing"] ? width-w : 0);
        BNPlace(child,CGRectMake(x,y,MIN(width,w),h));y+=h+_gap;
    }
}
@end

static NSDictionary *BNShortcutParts(NSString *shortcut) {
    NSArray *parts=[shortcut.lowercaseString componentsSeparatedByString:@"+"];NSString *key=parts.lastObject ?: @"";NSUInteger modifiers=0;
    for(NSString *part in parts){
#if TARGET_OS_OSX
        if([@[@"cmd",@"command",@"super"] containsObject:part])modifiers|=NSEventModifierFlagCommand;
        if([@[@"ctrl",@"control"] containsObject:part])modifiers|=NSEventModifierFlagControl;
        if([@[@"alt",@"option"] containsObject:part])modifiers|=NSEventModifierFlagOption;
        if([part isEqual:@"shift"])modifiers|=NSEventModifierFlagShift;
#else
        if([@[@"cmd",@"command",@"super"] containsObject:part])modifiers|=UIKeyModifierCommand;
        if([@[@"ctrl",@"control"] containsObject:part])modifiers|=UIKeyModifierControl;
        if([@[@"alt",@"option"] containsObject:part])modifiers|=UIKeyModifierAlternate;
        if([part isEqual:@"shift"])modifiers|=UIKeyModifierShift;
#endif
    }
    NSDictionary *named=@{@"space":@" ",@"enter":@"\r",@"return":@"\r",@"escape":@"\033",@"esc":@"\033",@"tab":@"\t",@"delete":@"\177",@"backspace":@"\177"};if(named[key])key=named[key];
#if TARGET_OS_OSX
    NSDictionary *arrows=@{@"left":[NSString stringWithFormat:@"%C",(unichar)NSLeftArrowFunctionKey],@"right":[NSString stringWithFormat:@"%C",(unichar)NSRightArrowFunctionKey],@"up":[NSString stringWithFormat:@"%C",(unichar)NSUpArrowFunctionKey],@"down":[NSString stringWithFormat:@"%C",(unichar)NSDownArrowFunctionKey]};
#else
    NSDictionary *arrows=@{@"left":UIKeyInputLeftArrow,@"right":UIKeyInputRightArrow,@"up":UIKeyInputUpArrow,@"down":UIKeyInputDownArrow};
#endif
    if(arrows[key])key=arrows[key];return @{@"input":key,@"modifiers":@(modifiers)};
}
static NSString *BNShortcutForControl(BNHost *host, BNControl *control) {
    return BNPropString(host,control.element,[control.element[@"kind"] isEqual:@"Shortcut"] ? @"key" : @"shortcut",control.locals);
}
@implementation BNRootView (Shortcuts)
#if TARGET_OS_OSX
-(BOOL)performKeyEquivalent:(NSEvent *)event {
    BNHost *host=[BNHost shared];NSUInteger mask=NSEventModifierFlagCommand|NSEventModifierFlagControl|NSEventModifierFlagOption|NSEventModifierFlagShift;
    if(!(event.modifierFlags&mask) && BNHandleSearchKey(host,self.context,event.charactersIgnoringModifiers.lowercaseString))return YES;
    for(BNControl *control in [host.controls copy]){if(!control.enabled || control.locals[@"__window"]!=self.context)continue;NSString *shortcut=BNShortcutForControl(host,control);if(!shortcut.length)continue;NSDictionary *parts=BNShortcutParts(shortcut);if(![parts[@"input"] isEqual:event.charactersIgnoringModifiers.lowercaseString] || [parts[@"modifiers"] unsignedIntegerValue]!=(event.modifierFlags&mask))continue;
        @try{[host performControl:control event:control.focus ? @"focus" : @"activate" value:BNNull()];}@catch(NSException *problem){[host showError:problem.reason];}return YES;
    }return [super performKeyEquivalent:event];
}
#else
-(NSArray<UIKeyCommand *> *)keyCommands {
    BNHost *host=[BNHost shared];NSMutableArray *commands=[BNSearchKeyCommands(host,self.context) mutableCopy];for(BNControl *control in host.controls){if(!control.enabled || control.locals[@"__window"]!=self.context)continue;NSString *shortcut=BNShortcutForControl(host,control);if(!shortcut.length)continue;NSDictionary *parts=BNShortcutParts(shortcut);
        UIKeyCommand *command=[UIKeyCommand commandWithTitle:control.label.length ? control.label : shortcut image:nil action:@selector(bnShortcut:) input:parts[@"input"] modifierFlags:[parts[@"modifiers"] unsignedIntegerValue] propertyList:control.target];[commands addObject:command];
    }return commands;
}
-(void)bnShortcut:(UIKeyCommand *)command {BNHost *host=[BNHost shared];for(BNControl *control in host.controls)if(control.locals[@"__window"]==self.context && [control.target isEqual:command.propertyList]){@try{[host performControl:control event:control.focus ? @"focus" : @"activate" value:BNNull()];}@catch(NSException *problem){[host showError:problem.reason];}break;}}
#endif
@end

@interface BNScroll : BNView
#if !TARGET_OS_OSX
<UIScrollViewDelegate>
#endif
@property(nonatomic,strong) BNLayout *document;
@property(nonatomic) BOOL horizontal;
@property(nonatomic) BOOL indicators;
@property(nonatomic) CGFloat openAt;
@property(nonatomic) BOOL positioned;
@property(nonatomic,weak) BNHost *host;
@property(nonatomic,strong) NSDictionary *element;
@property(nonatomic,strong) NSDictionary *locals;
@property(nonatomic,strong) id lastPosition;
@property(nonatomic,strong) NSArray *observers;
#if TARGET_OS_OSX
@property(nonatomic,strong) NSScrollView *scroll;
#else
@property(nonatomic,strong) UIScrollView *scroll;
#endif
@end
static void BNMotionScroll(BNHost *host, BNScroll *scroll);
@implementation BNScroll
-(void)setDocument:(BNLayout *)document {if(_document==document)return;[_document removeFromSuperview];_document=document;BNNeedsLayout(self);}
-(instancetype)initWithFrame:(CGRect)frame { if((self=[super initWithFrame:frame])) {
#if TARGET_OS_OSX
    _scroll=[[NSScrollView alloc] initWithFrame:CGRectZero];_scroll.drawsBackground=NO;_scroll.borderType=NSNoBorder;_scroll.autohidesScrollers=YES;_scroll.contentView.postsBoundsChangedNotifications=YES;__weak BNScroll *weakSelf=self;_observers=@[[NSNotificationCenter.defaultCenter addObserverForName:NSScrollViewDidEndLiveScrollNotification object:_scroll queue:NSOperationQueue.mainQueue usingBlock:^(NSNotification *notification){[weakSelf settled];}],[NSNotificationCenter.defaultCenter addObserverForName:NSViewBoundsDidChangeNotification object:_scroll.contentView queue:NSOperationQueue.mainQueue usingBlock:^(NSNotification *notification){BNScroll *owner=weakSelf;if(owner)BNMotionScroll(owner.host,owner);}]];
#else
    _scroll=[[UIScrollView alloc] initWithFrame:CGRectZero];_scroll.alwaysBounceVertical=NO;_scroll.delegate=self;
#endif
    _indicators=YES;[self addSubview:_scroll];
}return self;}
-(void)dealloc {for(id observer in _observers)[NSNotificationCenter.defaultCenter removeObserver:observer];}
-(NSArray<BNView *> *)items {
    NSMutableArray *items=[NSMutableArray array],*pending=[NSMutableArray arrayWithArray:_document.subviews];
    while(pending.count){BNView *view=pending.firstObject;[pending removeObjectAtIndex:0];if(!BNIsNull(BNMeta(view)[@"itemKey"]))[items addObject:view];else[pending addObjectsFromArray:view.subviews];}
    return items;
}
-(CGFloat)offsetFor:(BNView *)view center:(BOOL)center {
    CGRect rect=[view convertRect:view.bounds toView:_document];CGFloat start=_horizontal ? rect.origin.x : rect.origin.y,extent=_horizontal ? rect.size.width : rect.size.height,viewport=_horizontal ? self.bounds.size.width : self.bounds.size.height;
    return start+(center ? (extent-viewport)/2 : 0);
}
-(CGPoint)offsetPoint:(CGFloat)offset {
    CGFloat maximum=MAX(0,(_horizontal ? _document.bounds.size.width-self.bounds.size.width : _document.bounds.size.height-self.bounds.size.height));offset=MAX(0,MIN(maximum,offset));return CGPointMake(_horizontal ? offset : 0,_horizontal ? 0 : offset);
}
-(BNView *)nearest:(CGFloat)offset center:(BOOL)center {
    BNView *nearest=nil;CGFloat distance=CGFLOAT_MAX;for(BNView *view in [self items]){CGFloat delta=fabs([self offsetFor:view center:center]-offset);if(delta<distance){nearest=view;distance=delta;}}return nearest;
}
-(void)bnMoveTo:(CGPoint)point {
#if TARGET_OS_OSX
    [_scroll.contentView scrollToPoint:point];[_scroll reflectScrolledClipView:_scroll.contentView];
#else
    [_scroll setContentOffset:point animated:NO];
#endif
}
-(void)settled {
    NSString *snap=BNPropString(_host,_element,@"snap",_locals);BOOL center=[snap isEqual:@"center"];
#if TARGET_OS_OSX
    CGPoint point=_scroll.contentView.bounds.origin;
#else
    CGPoint point=_scroll.contentOffset;
#endif
    BNView *nearest=[self nearest:_horizontal ? point.x : point.y center:center];if(!nearest)return;
    if(snap.length)[self bnMoveTo:[self offsetPoint:[self offsetFor:nearest center:center]]];
    NSDictionary *field=BNDict(BNDict(_element[@"props"])[@"position"])[@"field"];id key=BNMeta(nearest)[@"itemKey"];
    if(field && !BNIsNull(key) && ![[_host field:field locals:_locals] isEqual:key]){_lastPosition=key;[_host setField:field value:key locals:_locals];}
}
#if !TARGET_OS_OSX
-(void)scrollViewDidScroll:(UIScrollView *)scrollView {BNMotionScroll(_host,self);}
-(void)scrollViewDidEndDragging:(UIScrollView *)scrollView willDecelerate:(BOOL)decelerate {if(!decelerate)[self settled];}
-(void)scrollViewDidEndDecelerating:(UIScrollView *)scrollView {[self settled];}
-(void)scrollViewWillEndDragging:(UIScrollView *)scrollView withVelocity:(CGPoint)velocity targetContentOffset:(inout CGPoint *)target {
    NSString *snap=BNPropString(_host,_element,@"snap",_locals);if(!snap.length)return;BNView *nearest=[self nearest:_horizontal ? target->x : target->y center:[snap isEqual:@"center"]];if(nearest)*target=[self offsetPoint:[self offsetFor:nearest center:[snap isEqual:@"center"]]];
}
#endif
#if TARGET_OS_OSX
-(BOOL)isFlipped{return YES;}
-(void)layout { [super layout];[self arrange]; }
#else
-(void)layoutSubviews { [super layoutSubviews];[self arrange]; }
#endif
-(void)arrange { _scroll.frame=self.bounds;CGSize bounds=self.bounds.size;
    CGSize size=[_document measure:CGSizeMake(_horizontal ? 100000 : bounds.width,_horizontal ? bounds.height : 100000)];
    size.width=MAX(size.width,bounds.width);size.height=MAX(size.height,bounds.height);
#if TARGET_OS_OSX
    _scroll.hasHorizontalScroller=_horizontal && _indicators;_scroll.hasVerticalScroller=!_horizontal && _indicators;
    if(_scroll.documentView!=_document)_scroll.documentView=_document;
#else
    _scroll.showsHorizontalScrollIndicator=_horizontal && _indicators;_scroll.showsVerticalScrollIndicator=!_horizontal && _indicators;
    if(_document.superview!=_scroll)[_scroll addSubview:_document];_scroll.contentSize=size;
#endif
    BNPlace(_document,CGRectMake(0,0,size.width,size.height));
    if(!_positioned) { _positioned=YES;CGFloat f=MAX(0,MIN(1,_openAt));CGPoint p=CGPointMake(_horizontal ? f*(size.width-bounds.width) : 0,_horizontal ? 0 : f*(size.height-bounds.height));
#if TARGET_OS_OSX
        [_scroll.contentView scrollToPoint:p];[_scroll reflectScrolledClipView:_scroll.contentView];
#else
        _scroll.contentOffset=p;
#endif
    }
    NSDictionary *field=BNDict(BNDict(_element[@"props"])[@"position"])[@"field"];id wanted=field ? [_host field:field locals:_locals] : nil;
    if(!BNIsNull(wanted) && ![_lastPosition isEqual:wanted]){_lastPosition=wanted;for(BNView *item in [self items])if([BNMeta(item)[@"itemKey"] isEqual:wanted]){[self bnMoveTo:[self offsetPoint:[self offsetFor:item center:YES]]];break;}}
    BNMotionScroll(_host,self);
}
@end

static CGSize BNMeasure(BNView *view, CGSize available) {
    NSDictionary *meta=BNMeta(view);CGFloat explicitWidth=[meta[@"width"] doubleValue],explicitHeight=[meta[@"height"] doubleValue];CGSize size=CGSizeZero;
    if([view isKindOfClass:BNLayout.class]) size=[(BNLayout *)view measure:available];
    else if([view isKindOfClass:BNScroll.class]) {BNScroll *s=(BNScroll *)view;CGSize content=[s.document measure:available];size=CGSizeMake(s.horizontal ? MIN(available.width,content.width) : available.width,s.horizontal ? content.height : MIN(available.height,content.height));}
    else {
#if TARGET_OS_OSX
        size=view.fittingSize;
        if([view isKindOfClass:NSTextField.class]) {NSTextField *label=(NSTextField *)view;BOOL wraps=!label.editable && label.maximumNumberOfLines!=1;
            if(wraps && available.width>0 && available.width<100000) {NSAttributedString *text=label.attributedStringValue;NSRect natural=[text boundingRectWithSize:CGSizeMake(100000,100000) options:NSStringDrawingUsesLineFragmentOrigin|NSStringDrawingUsesFontLeading];CGFloat chrome=MAX(0,label.cell.cellSize.width-natural.size.width);NSRect rect=[text boundingRectWithSize:CGSizeMake(MAX(0,available.width-chrome),100000) options:NSStringDrawingUsesLineFragmentOrigin|NSStringDrawingUsesFontLeading];size=CGSizeMake(MIN(available.width,ceil(rect.size.width+chrome)),ceil(rect.size.height));if(label.maximumNumberOfLines>0)size.height=MIN(size.height,label.maximumNumberOfLines*(label.font.pointSize+3));}
        }
#else
        size=[view sizeThatFits:CGSizeMake(MAX(0,available.width),MAX(0,available.height))];
        if(size.width<=0 || size.height<=0) {CGSize intrinsic=view.intrinsicContentSize;if(size.width<=0)size.width=MAX(0,intrinsic.width);if(size.height<=0)size.height=MAX(0,intrinsic.height);}
#endif
    }
    NSArray *minimum=BNArray(meta[@"minimumSize"]);if(minimum.count==2){size.width=MAX(size.width,[minimum[0] doubleValue]);size.height=MAX(size.height,[minimum[1] doubleValue]);}
    if([meta[@"fillWidth"] boolValue] && available.width<100000)size.width=available.width;
    if([meta[@"fillHeight"] boolValue] && available.height<100000)size.height=available.height;
    if(explicitWidth>0)size.width=explicitWidth;if(explicitHeight>0)size.height=explicitHeight;
    CGFloat aspect=[meta[@"pictureAspect"] doubleValue];if(aspect>0){if(explicitHeight<=0){size.width=MIN(size.width,available.width);size.height=size.width/aspect;}else if(explicitWidth<=0)size.width=size.height*aspect;}
    if([meta[@"kind"] isEqual:@"Spacer"]){size=CGSizeZero;}
    return CGSizeMake(BNFinite(size.width),BNFinite(size.height));
}
static void BNPlace(BNView *view, CGRect rect) {
    rect.size.width=BNFinite(rect.size.width);rect.size.height=BNFinite(rect.size.height);view.frame=rect;
    if([view isKindOfClass:BNLayout.class])[(BNLayout *)view arrange];
    else if([view isKindOfClass:BNScroll.class])[(BNScroll *)view arrange];
    BNDecorations(view);BNNeedsLayout(view);
}
static void BNConfigureForm(BNHost *host, BNScroll *scroll, NSDictionary *element, NSDictionary *locals) {
    CGFloat defaultX=BNPropNumber(host,element,@"padding_x",locals,0),defaultY=BNPropNumber(host,element,@"padding_y",locals,0),minimum=BNPropNumber(host,element,@"row_height",locals,0);
    for(BNView *section in [scroll.document.subviews copy]){NSDictionary *meta=BNMeta(section),*definition=BNDict(meta[@"element"]),*scope=BNDict(meta[@"locals"]);BOOL group=[definition[@"kind"] isEqual:@"Section"],plain=group && [BNPropString(host,definition,@"style",scope) isEqual:@"plain"];CGFloat x=BNPropNumber(host,definition,@"padding_x",scope,plain ? 0 : defaultX),y=BNPropNumber(host,definition,@"padding_y",scope,plain ? 0 : defaultY);
        if(group && [section isKindOfClass:BNLayout.class]){((BNLayout *)section).paddingX=0;((BNLayout *)section).paddingY=0;NSArray *rows=[section.subviews copy];for(BNView *row in rows){if([BNMeta(row)[@"sectionAnnotation"] boolValue])continue;NSUInteger index=[section.subviews indexOfObject:row];[row removeFromSuperview];BNLayout *wrapper=BNContainer(@"row",0);wrapper.fillWidth=YES;wrapper.paddingX=x;wrapper.paddingY=y;[wrapper addSubview:row];BNSetMeta(wrapper,@{@"minimumSize":@[@0,@(plain ? 0 : minimum)],@"fillWidth":@YES});
#if TARGET_OS_OSX
            if(index<section.subviews.count)[section addSubview:wrapper positioned:NSWindowBelow relativeTo:section.subviews[index]];else[section addSubview:wrapper];
#else
            [section insertSubview:wrapper atIndex:MIN(index,section.subviews.count)];
#endif
        }}
    }
}

static NSString *BNSourceURL(id source) {
    if(BNIsNull(source))return nil;
    if([source isKindOfClass:NSString.class])return source;
    if([source isKindOfClass:NSArray.class])return BNString(BNAt(source,0));
    NSDictionary *record=BNDict(source);return BNString(record[@"url"] ?: BNAt(BNArray(record[@"fields"]),0));
}
static id BNLoadPicture(BNHost *host, NSString *source) {
    if(!source.length)return nil;NSURL *url=[NSURL URLWithString:source];
    if(!url.scheme.length)url=[NSURL fileURLWithPath:[NSBundle.mainBundle.resourcePath stringByAppendingPathComponent:source]];
    static NSCache *cache;static NSMutableSet *loading;static dispatch_once_t once;dispatch_once(&once,^{cache=[NSCache new];cache.countLimit=128;loading=[NSMutableSet set];});NSString *key=url.absoluteString;
    id image=[cache objectForKey:key];if(image)return BNIsNull(image) ? nil : image;
    if(url.isFileURL){
#if TARGET_OS_OSX
        image=[[NSImage alloc] initWithContentsOfURL:url];
#else
        image=[UIImage imageWithContentsOfFile:url.path];
#endif
        [cache setObject:image ?: BNNull() forKey:key];return image;
    }
    if(![@[@"https",@"http"] containsObject:url.scheme.lowercaseString] || [loading containsObject:key])return nil;
    [loading addObject:key];__weak BNHost *weakHost=host;
    [[NSURLSession.sharedSession dataTaskWithURL:url completionHandler:^(NSData *data,NSURLResponse *response,NSError *error){dispatch_async(dispatch_get_main_queue(),^{
#if TARGET_OS_OSX
        NSImage *loaded=data ? [[NSImage alloc] initWithData:data] : nil;
#else
        UIImage *loaded=data ? [UIImage imageWithData:data] : nil;
#endif
        [cache setObject:loaded ?: BNNull() forKey:key];[loading removeObject:key];[weakHost scheduleRender];
    });}] resume];return nil;
}
static BNColor *BNPictureAverage(BNHost *host, NSString *source) {
    id image=BNLoadPicture(host,source);if(!image)return nil;CGImageRef pixels=NULL;
#if TARGET_OS_OSX
    pixels=[image CGImageForProposedRect:NULL context:nil hints:nil];
#else
    pixels=[image CGImage];
#endif
    if(!pixels)return nil;unsigned char rgba[4]={0};CGColorSpaceRef space=CGColorSpaceCreateDeviceRGB();CGContextRef bitmap=CGBitmapContextCreate(rgba,1,1,8,4,space,kCGImageAlphaPremultipliedLast);CGColorSpaceRelease(space);if(!bitmap)return nil;CGContextDrawImage(bitmap,CGRectMake(0,0,1,1),pixels);CGContextRelease(bitmap);CGFloat alpha=rgba[3]/255.0;if(alpha<=0)return nil;
#if TARGET_OS_OSX
    return [NSColor colorWithSRGBRed:MIN(1,rgba[0]/255.0/alpha) green:MIN(1,rgba[1]/255.0/alpha) blue:MIN(1,rgba[2]/255.0/alpha) alpha:1];
#else
    return [UIColor colorWithRed:MIN(1,rgba[0]/255.0/alpha) green:MIN(1,rgba[1]/255.0/alpha) blue:MIN(1,rgba[2]/255.0/alpha) alpha:1];
#endif
}
#if TARGET_OS_OSX
// NSImageView supplies image drawing and tinting. The wrapper only supplies
// the aspect-fill crop, which NSImageScaling does not provide on AppKit.
@interface BNPictureView : NSView
@property(nonatomic,strong) NSImage *image;
@property(nonatomic,strong) NSImageView *picture;
@property(nonatomic,strong) NSString *fit;
@property(nonatomic) BOOL templateImage;
@end
@implementation BNPictureView
-(instancetype)initWithFrame:(NSRect)frame {if((self=[super initWithFrame:frame])){_picture=[[NSImageView alloc]initWithFrame:NSZeroRect];_picture.imageAlignment=NSImageAlignCenter;[self addSubview:_picture];self.wantsLayer=YES;self.layer.masksToBounds=YES;}return self;}
-(BOOL)isFlipped{return YES;}
-(NSSize)intrinsicContentSize{return _image ? _image.size : NSMakeSize(100,100);}
-(void)setImage:(NSImage *)image {_image=image;[self updatePicture];[self invalidateIntrinsicContentSize];}
-(void)setTemplateImage:(BOOL)templateImage {_templateImage=templateImage;[self updatePicture];}
-(void)setFit:(NSString *)fit {_fit=fit;self.needsLayout=YES;}
-(void)updatePicture {NSImage *image=_image;if(_templateImage&&image){image=[image copy];image.template=YES;}_picture.image=image;_picture.contentTintColor=_templateImage ? BNRole(@"icon.primary") : nil;self.needsLayout=YES;}
-(void)layout {[super layout];NSRect rect=self.bounds;NSSize natural=_image.size;if([_fit isEqual:@"cover"]&&natural.width>0&&natural.height>0){CGFloat scale=MAX(rect.size.width/natural.width,rect.size.height/natural.height);NSSize size=NSMakeSize(natural.width*scale,natural.height*scale);rect=NSMakeRect((rect.size.width-size.width)/2,(rect.size.height-size.height)/2,size.width,size.height);_picture.imageScaling=NSImageScaleAxesIndependently;}else _picture.imageScaling=[_fit isEqual:@"fill"] ? NSImageScaleAxesIndependently : NSImageScaleProportionallyUpOrDown;_picture.frame=rect;}
@end
#else
@interface BNPictureView : UIImageView
@property(nonatomic,strong) NSString *fit;
@property(nonatomic) BOOL templateImage;
@end
@implementation BNPictureView
-(instancetype)initWithFrame:(CGRect)frame {if((self=[super initWithFrame:frame])){self.contentMode=UIViewContentModeScaleAspectFit;self.clipsToBounds=YES;}return self;}
-(void)setFit:(NSString *)fit {_fit=fit;self.contentMode=[fit isEqual:@"cover"] ? UIViewContentModeScaleAspectFill : [fit isEqual:@"fill"] ? UIViewContentModeScaleToFill : UIViewContentModeScaleAspectFit;}
-(void)setTemplateImage:(BOOL)templateImage {_templateImage=templateImage;[self setImage:self.image];}
-(void)setImage:(UIImage *)image {[super setImage:[image imageWithRenderingMode:_templateImage ? UIImageRenderingModeAlwaysTemplate : UIImageRenderingModeAlwaysOriginal]];if(_templateImage)self.tintColor=BNRole(@"icon.primary");}
-(CGSize)sizeThatFits:(CGSize)size {CGSize natural=self.image ? self.image.size : CGSizeMake(100,100);CGFloat scale=natural.width>0 ? MIN(1,size.width/natural.width) : 1;return CGSizeMake(natural.width*scale,natural.height*scale);}
@end
#endif

@interface BNFieldDelegate : NSObject
#if TARGET_OS_OSX
<NSTextFieldDelegate,NSTextViewDelegate>
#else
<UITextFieldDelegate,UITextViewDelegate>
#endif
@property(nonatomic,strong) BNControl *control;
@end
@implementation BNFieldDelegate
#if TARGET_OS_OSX
-(void)controlTextDidChange:(NSNotification *)notification {if(_control.edit)_control.edit([notification.object stringValue]);}
-(void)textDidChange:(NSNotification *)notification {if(_control.edit)_control.edit([notification.object string]);}
-(BOOL)control:(NSControl *)control textView:(NSTextView *)textView doCommandBySelector:(SEL)command {if(command==@selector(insertNewline:)){if(_control.submit)_control.submit();return YES;}return NO;}
#else
-(BOOL)textFieldShouldReturn:(UITextField *)field {if(_control.submit)_control.submit();return YES;}
-(void)textViewDidChange:(UITextView *)view {if(_control.edit)_control.edit(view.text);}
#endif
@end

static id BNControlValue(BNHost *host, NSDictionary *element, NSString *controlled, NSDictionary *locals) {
    NSDictionary *field=BNDict(BNDict(element[@"props"])[@"value"])[@"field"];
    return field ? [host field:field locals:locals] : [host prop:element name:controlled locals:locals];
}
static void BNSetControlValue(BNHost *host, NSDictionary *element, NSDictionary *locals, id value) {
    NSString *kind=BNString(element[@"kind"]);
    NSString *property=!BNIsNull(BNDict(element[@"props"])[@"value"]) ? @"value" : [kind isEqual:@"Switch"] || [kind isEqual:@"SplitButton"] ? @"checked" : [kind isEqual:@"Slider"] ? @"current" : @"selected";
    [host commit:element property:property value:value locals:locals];
}
static void BNEndEditing(BNView *view) {
#if TARGET_OS_OSX
    [view.window makeFirstResponder:nil];
#else
    [view endEditing:YES];
#endif
}
static void BNFire(BNHost *host, NSDictionary *element, NSDictionary *locals, BNView *view) {
    if(BNSearchBeforeFire(host,element,locals,view))return;
    if(!BNIsNull(element[@"action"])) [host action:element[@"action"] locals:locals];
    NSDictionary *props=BNDict(element[@"props"]),*field=BNDict(props[@"clears"])[@"field"];
    if([BNPropString(host,element,@"submit",locals) isEqual:@"clear"])field=BNDict(props[@"value"])[@"field"];
    if(field){[host setField:field value:@"" locals:locals];BNEndEditing(view);}
}
#if TARGET_OS_OSX
@interface BNStyledButton : NSButton
@property(nonatomic,copy) void (^feedback)(NSString *);
@property(nonatomic,strong) NSTrackingArea *bernTracking;
@property(nonatomic) CGFloat bernPadding;
@property(nonatomic,strong) BNLayout *customContent;
@property(nonatomic,strong) BNView *badge;
@end
@implementation BNStyledButton
-(NSSize)intrinsicContentSize {if(_customContent)return [_customContent measure:CGSizeMake(100000,100000)];NSSize size=[super intrinsicContentSize];if(_bernPadding>0){size.width+=2*_bernPadding;size.height+=2*_bernPadding;}if(_badge)size.width+=_badge.fittingSize.width+12;return size;}
-(void)setCustomContent:(BNLayout *)content {[_customContent removeFromSuperview];_customContent=content;if(content){[self addSubview:content];[self invalidateIntrinsicContentSize];}}
-(NSView *)hitTest:(NSPoint)point {NSView *hit=[super hitTest:point];return _customContent && hit ? self : hit;}
-(void)layout {[super layout];if(_customContent)BNPlace(_customContent,self.bounds);if(_badge){CGSize size=_badge.fittingSize;_badge.frame=CGRectMake(MAX(0,self.bounds.size.width-size.width-8),(self.bounds.size.height-size.height)/2,size.width,size.height);}}

-(void)updateTrackingAreas {[super updateTrackingAreas];if(_bernTracking)[self removeTrackingArea:_bernTracking];_bernTracking=[[NSTrackingArea alloc] initWithRect:self.bounds options:NSTrackingMouseEnteredAndExited|NSTrackingActiveInKeyWindow|NSTrackingInVisibleRect owner:self userInfo:nil];[self addTrackingArea:_bernTracking];}
-(void)mouseEntered:(NSEvent *)event {if(_feedback)_feedback(@"hover");}
-(void)mouseExited:(NSEvent *)event {if(_feedback)_feedback(@"");}
-(void)mouseDown:(NSEvent *)event {BNHost *host=[BNHost shared];[host beginInteraction];@try{if(_feedback)_feedback(@"pressed");[super mouseDown:event];if(_feedback)_feedback(@"");}@finally{[host endInteraction];}}
-(BOOL)becomeFirstResponder {BOOL result=[super becomeFirstResponder];if(result&&_feedback)_feedback(@"focus");return result;}
-(BOOL)resignFirstResponder {BOOL result=[super resignFirstResponder];if(result&&_feedback)_feedback(@"");return result;}
@end
#else
@interface BNStyledButton : UIButton
@property(nonatomic,copy) void (^feedback)(NSString *);
@property(nonatomic,strong) BNLayout *customContent;
@property(nonatomic,strong) BNView *badge;
@end
@implementation BNStyledButton
-(void)setCustomContent:(BNLayout *)content {[_customContent removeFromSuperview];_customContent=content;if(content){[self addSubview:content];[self invalidateIntrinsicContentSize];}}
-(CGSize)intrinsicContentSize {if(_customContent)return [_customContent measure:CGSizeMake(100000,100000)];CGSize size=[super intrinsicContentSize];if(_badge)size.width+=[_badge sizeThatFits:CGSizeMake(100000,100000)].width+12;return size;}
-(CGSize)sizeThatFits:(CGSize)size {return _customContent ? [_customContent measure:size] : [super sizeThatFits:size];}
-(UIView *)hitTest:(CGPoint)point withEvent:(UIEvent *)event {UIView *hit=[super hitTest:point withEvent:event];return _customContent && hit ? self : hit;}
-(void)layoutSubviews {[super layoutSubviews];if(_customContent)BNPlace(_customContent,self.bounds);if(_badge){CGSize size=[_badge sizeThatFits:self.bounds.size];_badge.frame=CGRectMake(MAX(0,self.bounds.size.width-size.width-8),(self.bounds.size.height-size.height)/2,size.width,size.height);}}
-(void)setHighlighted:(BOOL)highlighted {[super setHighlighted:highlighted];if(_feedback)_feedback(highlighted ? @"pressed" : @"");}
-(void)didUpdateFocusInContext:(UIFocusUpdateContext *)context withAnimationCoordinator:(UIFocusAnimationCoordinator *)coordinator {[super didUpdateFocusInContext:context withAnimationCoordinator:coordinator];if(_feedback)_feedback(self.isFocused ? @"focus" : @"");}
@end
#endif
static BNView *BNMakeButton(NSString *label, NSString *icon, BNControl *control, BOOL plain) {
#if TARGET_OS_OSX
    BNStyledButton *button=[BNStyledButton buttonWithTitle:label target:control action:@selector(clicked:)];
    button.bezelStyle=NSBezelStyleRounded;button.bordered=!plain;button.font=[NSFont systemFontOfSize:13];
    if(icon.length){button.image=[NSImage imageWithSystemSymbolName:icon accessibilityDescription:label];button.imagePosition=label.length ? NSImageLeading : NSImageOnly;}
#else
    BNStyledButton *button=[BNStyledButton buttonWithType:UIButtonTypeSystem];[button setTitle:label forState:UIControlStateNormal];
    button.titleLabel.font=[UIFont systemFontOfSize:17];button.contentEdgeInsets=UIEdgeInsetsMake(6,10,6,10);
    if(icon.length){[button setImage:[UIImage systemImageNamed:icon] forState:UIControlStateNormal];if(label.length)button.imageEdgeInsets=UIEdgeInsetsMake(0,-4,0,4);}
    [button addTarget:control action:@selector(clicked:) forControlEvents:UIControlEventTouchUpInside];
#endif
    BNKeep(button,control);return button;
}

@interface BNFilePicker : NSObject
#if !TARGET_OS_OSX
<UIDocumentPickerDelegate>
#endif
@property(nonatomic,copy) void (^receive)(NSURL *);
@property(nonatomic,weak) BNHost *host;
@end
@implementation BNFilePicker
#if !TARGET_OS_OSX
-(void)documentPicker:(UIDocumentPickerViewController *)controller didPickDocumentsAtURLs:(NSArray<NSURL *> *)urls {@try{if(urls.count && _receive)_receive(urls.firstObject);}@catch(NSException *problem){[_host showError:problem.reason];}}
#endif
@end
static void BNChooseFile(BNHost *host, NSDictionary *element, NSDictionary *locals, BNView *anchor, void (^receive)(NSURL *)) {
    NSString *kinds=BNPropString(host,element,@"files",locals);NSArray *words=[kinds componentsSeparatedByCharactersInSet:NSCharacterSet.whitespaceCharacterSet];
#if TARGET_OS_OSX
    NSOpenPanel *panel=[NSOpenPanel openPanel];panel.canChooseDirectories=[words containsObject:@"folder"];panel.canChooseFiles=!(words.count==1 && [words containsObject:@"folder"]);panel.allowsMultipleSelection=NO;
    NSArray<UTType *> *types=BNFileTypes(host,kinds);if(types.count)panel.allowedContentTypes=types;
    if(anchor.window)[panel beginSheetModalForWindow:anchor.window completionHandler:^(NSModalResponse result){@try{if(result==NSModalResponseOK && panel.URL)receive(panel.URL);}@catch(NSException *problem){[host showError:problem.reason];}}];
    else if([panel runModal]==NSModalResponseOK && panel.URL){@try{receive(panel.URL);}@catch(NSException *problem){[host showError:problem.reason];}}
#else
    NSArray<UTType *> *types=BNFileTypes(host,kinds);if(!types.count)types=@[UTTypeItem];UIDocumentPickerViewController *picker=[[UIDocumentPickerViewController alloc] initForOpeningContentTypes:types asCopy:NO];picker.allowsMultipleSelection=NO;
    BNFilePicker *delegate=[BNFilePicker new];delegate.host=host;delegate.receive=receive;picker.delegate=delegate;objc_setAssociatedObject(picker,BNRetainedKey,delegate,OBJC_ASSOCIATION_RETAIN_NONATOMIC);
    UIViewController *controller=anchor.window.rootViewController;while(controller.presentedViewController)controller=controller.presentedViewController;
    if(controller)[controller presentViewController:picker animated:YES completion:nil];
#endif
}
static void BNInstallFileAction(BNHost *host, BNControl *control, NSDictionary *element, NSDictionary *locals, BNView *view) {
    NSDictionary *field=BNDict(BNDict(element[@"props"])[@"pick"])[@"field"];if(!field)return;
    __weak BNHost *weakHost=host;__weak BNView *anchor=view;
    void (^receive)(NSURL *)=^(NSURL *url){
        if(!url)return;BNHost *owner=weakHost;if(!owner)return;
        NSString *kinds=BNPropString(owner,element,@"files",locals);if(!BNFileAccepts(owner,url,kinds))BNThrow(@"invalid_file",@"The selected file does not match the control's accepted file kinds");BNRememberURL(url);
        // MediaSource is the framework's one-field record, shared with Rust.
        [owner setField:field value:@[url.absoluteString] locals:locals];BNFire(owner,element,locals,anchor);
    };
    control.setFile=receive;control.activate=^{BNChooseFile(weakHost,element,locals,anchor,receive);};
}

@interface BNPopoverOwner : NSObject
#if TARGET_OS_OSX
<NSPopoverDelegate>
@property(nonatomic,strong) NSPopover *popover;
#else
<UIPopoverPresentationControllerDelegate>
@property(nonatomic,strong) UIViewController *controller;
#endif
@property(nonatomic,weak) BNHost *host;
@property(nonatomic,strong) NSDictionary *field;
@property(nonatomic,strong) NSDictionary *locals;
@property(nonatomic,weak) BNWindow *window;
@property(nonatomic,weak) BNView *anchor;
@property(nonatomic,strong) NSString *key;
@end
static const void *BNPopoverRegistryKey=&BNPopoverRegistryKey;
static NSMutableDictionary *BNPopovers(BNHost *host) {NSMutableDictionary *owners=objc_getAssociatedObject(host,BNPopoverRegistryKey);if(!owners){owners=[NSMutableDictionary dictionary];objc_setAssociatedObject(host,BNPopoverRegistryKey,owners,OBJC_ASSOCIATION_RETAIN_NONATOMIC);}return owners;}
static NSString *BNPopoverIdentity(NSDictionary *element, NSDictionary *locals) {BNWindow *window=locals[@"__window"];return [NSString stringWithFormat:@"%@/%@/%@%@",window.identifier,locals[@"__component"] ?: @"",element[@"path"],locals[@"__keys"] ?: @""];}
@implementation BNPopoverOwner
-(void)closed {if(_field && _window){NSMutableDictionary *scope=[_locals mutableCopy];scope[@"__window"]=_window;if([[_host field:_field locals:scope] boolValue])[_host setField:_field value:@NO locals:scope];}[BNPopovers(_host) removeObjectForKey:_key];}
#if TARGET_OS_OSX
-(void)popoverDidClose:(NSNotification *)notification {[self closed];_popover=nil;}
#else
-(UIModalPresentationStyle)adaptivePresentationStyleForPresentationController:(UIPresentationController *)controller {return UIModalPresentationNone;}
-(void)presentationControllerDidDismiss:(UIPresentationController *)controller {[self closed];_controller=nil;}
#endif
@end
static BNView *BNFindIdentifier(BNView *view, NSString *identifier) {if(!identifier.length)return nil;
#if TARGET_OS_OSX
    if([view.accessibilityIdentifier isEqual:identifier])return view;
#else
    if([view.accessibilityIdentifier isEqual:identifier])return view;
#endif
    for(BNView *child in view.subviews){BNView *found=BNFindIdentifier(child,identifier);if(found)return found;}return nil;
}
static void BNDismissPopover(BNHost *host, NSDictionary *element, NSDictionary *locals) {NSString *key=BNPopoverIdentity(element,locals);BNPopoverOwner *owner=BNPopovers(host)[key];if(!owner)return;
#if TARGET_OS_OSX
    [owner.popover close];
#else
    [owner.controller dismissViewControllerAnimated:NO completion:nil];[owner closed];
#endif
    [BNPopovers(host) removeObjectForKey:key];
}
static void BNPopoverPrune(BNHost *host, BOOL stop) {for(BNPopoverOwner *owner in [BNPopovers(host).allValues copy]){BNWindow *window=owner.window;BOOL active=window && host.windows[window.definition[@"id"]]==window;if(!stop && active)continue;owner.field=nil;
#if TARGET_OS_OSX
    [owner.popover close];
#else
    [owner.controller dismissViewControllerAnimated:NO completion:nil];
#endif
    [BNPopovers(host) removeObjectForKey:owner.key];}}
static void BNShowPopover(BNHost *host, NSDictionary *element, NSDictionary *locals, BNView *anchor) {
    if(!anchor.window)return;
    NSString *key=BNPopoverIdentity(element,locals);BNPopoverOwner *existing=BNPopovers(host)[key];
    BNLayout *content=BNContainer(@"column",8);content.padding=12;for(BNView *child in BNRendered(host,element[@"children"],locals))[content addSubview:child];
    CGFloat width=BNPropNumber(host,element,@"width",locals,320);CGSize size=[content measure:CGSizeMake(width,600)];size.width=MAX(100,MIN(600,size.width));size.height=MAX(40,MIN(600,size.height));
    BNPlace(content,CGRectMake(0,0,size.width,size.height));
    BNPopoverOwner *owner=existing ?: [BNPopoverOwner new];owner.host=host;owner.window=locals[@"__window"];NSMutableDictionary *scope=[locals mutableCopy];[scope removeObjectForKey:@"__window"];owner.locals=scope;owner.field=BNDict(BNDict(element[@"props"])[@"presented"])[@"field"];owner.anchor=anchor;owner.key=key;BNPopovers(host)[key]=owner;
#if TARGET_OS_OSX
    if(existing.popover.shown){NSResponder *responder=existing.popover.contentViewController.view.window.firstResponder;NSView *focused=[responder isKindOfClass:NSTextView.class] && [(NSTextView *)responder isFieldEditor] ? (id)[(NSTextView *)responder delegate] : [responder isKindOfClass:NSView.class] ? (NSView *)responder : nil;NSString *identity=focused.accessibilityIdentifier;NSRange selection=[responder isKindOfClass:NSTextView.class] ? [(NSTextView *)responder selectedRange] : NSMakeRange(NSNotFound,0);existing.popover.contentViewController.view=content;existing.popover.contentSize=size;BNView *replacement=BNFindIdentifier(content,identity);if(replacement){[content.window makeFirstResponder:replacement];if(selection.location!=NSNotFound && [content.window.firstResponder isKindOfClass:NSTextView.class])[(NSTextView *)content.window.firstResponder setSelectedRange:selection];}BNKeep(anchor,owner);return;}
    NSViewController *controller=[NSViewController new];controller.view=content;NSPopover *popover=[NSPopover new];popover.behavior=NSPopoverBehaviorTransient;popover.contentViewController=controller;popover.contentSize=size;popover.delegate=owner;owner.popover=popover;
    BNKeep(anchor,owner);[popover showRelativeToRect:anchor.bounds ofView:anchor preferredEdge:NSRectEdgeMaxY];
#else
    if(existing.controller.presentingViewController){UIView *focused=nil;NSMutableArray *pending=[NSMutableArray arrayWithObject:existing.controller.view];while(pending.count){UIView *candidate=pending.firstObject;[pending removeObjectAtIndex:0];if(candidate.isFirstResponder){focused=candidate;break;}[pending addObjectsFromArray:candidate.subviews];}NSString *identity=focused.accessibilityIdentifier;existing.controller.view=content;existing.controller.preferredContentSize=size;existing.controller.popoverPresentationController.sourceView=anchor;existing.controller.popoverPresentationController.sourceRect=anchor.bounds;[BNFindIdentifier(content,identity) becomeFirstResponder];BNKeep(anchor,owner);return;}
    UIViewController *controller=[UIViewController new];controller.view=content;controller.preferredContentSize=size;controller.modalPresentationStyle=UIModalPresentationPopover;
    owner.controller=controller;BNKeep(anchor,owner);controller.popoverPresentationController.sourceView=anchor;controller.popoverPresentationController.sourceRect=anchor.bounds;controller.popoverPresentationController.delegate=owner;
    UIViewController *presenter=anchor.window.rootViewController;while(presenter.presentedViewController)presenter=presenter.presentedViewController;[presenter presentViewController:controller animated:YES completion:nil];
#endif
}

@interface BNClock : NSObject
@property(nonatomic,strong) NSTimer *timer;
@property(nonatomic,weak) BNHost *host;
@property(nonatomic,weak) BNWindow *window;
@property(nonatomic,strong) NSDictionary *element;
@property(nonatomic,strong) NSDictionary *locals;
@property(nonatomic) NSTimeInterval touched;
@property(nonatomic) NSTimeInterval interval;
@property(nonatomic,weak) BNView *view;
@end
@implementation BNClock
-(void)dealloc {[_timer invalidate];}
-(void)fire {if(!_host.handle || !_window || !_view.window){[_timer invalidate];_timer=nil;return;}NSMutableDictionary *locals=[_locals mutableCopy];locals[@"__window"]=_window;@try{[_host action:_element[@"action"] locals:locals];}@catch(NSException *error){[_host showError:error.reason];}}
@end
static void BNInstallTimer(BNHost *host, NSDictionary *element, NSDictionary *locals, BNView *view) {
    static NSMapTable<NSString *,BNClock *> *clocks;static dispatch_once_t once;dispatch_once(&once,^{clocks=[NSMapTable strongToWeakObjectsMapTable];});
    BNWindow *window=locals[@"__window"];NSString *key=[NSString stringWithFormat:@"%p:%@:%@:%@",host,window.identifier,element[@"path"],locals[@"__keys"]];
    BNClock *clock=[clocks objectForKey:key];BOOL enabled=BNPropBool(host,element,@"enabled",locals,YES);
    if(!enabled){[clock.timer invalidate];[clocks removeObjectForKey:key];return;}
    CGFloat interval=MAX(0.001,BNPropNumber(host,element,@"interval",locals,1));
    if(!clock){clock=[BNClock new];[clocks setObject:clock forKey:key];}clock.host=host;clock.window=window;clock.view=view;clock.element=element;NSMutableDictionary *scope=[locals mutableCopy];[scope removeObjectForKey:@"__window"];clock.locals=scope;clock.touched=NSDate.timeIntervalSinceReferenceDate;
    if(!clock.timer || clock.interval!=interval){[clock.timer invalidate];clock.interval=interval;__weak BNClock *weakClock=clock;clock.timer=[NSTimer scheduledTimerWithTimeInterval:interval repeats:YES block:^(NSTimer *timer){[weakClock fire];}];}
    BNKeep(view,clock);
}

// Canvas uses CoreGraphics on both Apple platforms instead of SwiftUI.Canvas.
@interface BNCanvasView : BNView
@property(nonatomic,weak) BNHost *host;
@property(nonatomic,strong) NSArray *drawings;
@property(nonatomic,strong) NSDictionary *locals;
@end
@implementation BNCanvasView
#if TARGET_OS_OSX
-(BOOL)isFlipped{return YES;}
-(void)drawRect:(NSRect)dirtyRect {CGContextRef context=NSGraphicsContext.currentContext.CGContext;[self paint:context];}
#else
-(void)drawRect:(CGRect)dirtyRect {[self paint:UIGraphicsGetCurrentContext()];}
#endif
-(void)paint:(CGContextRef)context {
    if(!context)return;
    for(NSDictionary *node in _drawings){NSDictionary *element=BNDict(node);NSString *kind=element[@"kind"];
        CGFloat opacity=BNPropNumber(_host,element,@"opacity",_locals,1);CGContextSaveGState(context);CGContextSetAlpha(context,opacity);
        NSString *fill=BNPropString(_host,element,@"fill",_locals),*stroke=BNPropString(_host,element,@"stroke",_locals);
        CGMutablePathRef path=CGPathCreateMutable();CGPathRef strokePath=NULL;
        if([kind isEqual:@"Shape"]){CGFloat x=BNPropNumber(_host,element,@"x",_locals,0),y=BNPropNumber(_host,element,@"y",_locals,0);
            CGRect rect=CGRectMake(x,y,BNPropNumber(_host,element,@"width",_locals,self.bounds.size.width-x),BNPropNumber(_host,element,@"height",_locals,self.bounds.size.height-y));
            NSString *shape=BNPropString(_host,element,@"kind",_locals);CGFloat corner=BNPropNumber(_host,element,@"corner",_locals,8);
            if([shape isEqual:@"ellipse"])CGPathAddEllipseInRect(path,NULL,rect);
            else if([shape isEqual:@"rounded"] || [shape isEqual:@"capsule"]){if([shape isEqual:@"capsule"])corner=MIN(rect.size.width,rect.size.height)/2;CGPathAddRoundedRect(path,NULL,rect,corner,corner);}
            else CGPathAddRect(path,NULL,rect);
        }else if([kind isEqual:@"Series"]){NSArray *values=BNArray([_host prop:element name:@"values" locals:_locals]);CGFloat top=BNPropNumber(_host,element,@"max",_locals,0);
            if(top<=0)for(NSNumber *n in values)top=MAX(top,[n doubleValue]);top=MAX(1,top);
            for(NSUInteger i=0;i<values.count;i++){CGPoint point=CGPointMake(values.count>1 ? self.bounds.size.width*i/(values.count-1) : self.bounds.size.width/2,self.bounds.size.height*(1-MAX(0,MIN(1,[values[i] doubleValue]/top))));if(i==0)CGPathMoveToPoint(path,NULL,point.x,point.y);else CGPathAddLineToPoint(path,NULL,point.x,point.y);}
            BOOL area=[BNPropString(_host,element,@"kind",_locals) isEqual:@"area"];if(area){strokePath=CGPathCreateCopy(path);CGPathAddLineToPoint(path,NULL,values.count>1 ? self.bounds.size.width : self.bounds.size.width/2,self.bounds.size.height);CGPathAddLineToPoint(path,NULL,values.count>1 ? 0 : self.bounds.size.width/2,self.bounds.size.height);CGPathCloseSubpath(path);if(!fill.length)fill=@"accent";}else if(!stroke.length)stroke=@"accent";
        }else if([kind isEqual:@"Pattern"]){NSString *name=BNPropString(_host,element,@"name",_locals);NSDictionary *pattern=nil;for(NSDictionary *p in BNArray(BNDict(_host.model[@"style"])[@"patterns"]))if([p[@"name"] isEqual:name])pattern=p;
            NSArray *bands=BNArray(pattern[@"bands"]);CGFloat period=0;for(NSDictionary *band in bands)period+=MAX(0,[band[@"width"] doubleValue]);
            if(period>0){for(CGFloat x=0;x<self.bounds.size.width;x+=period){CGFloat at=x;for(NSDictionary *band in bands){CGFloat w=MAX(0,[band[@"width"] doubleValue]);if(!BNIsNull(band[@"color"])){CGContextSetFillColorWithColor(context,BNColorRef(band[@"color"],self).CGColor);CGContextSetAlpha(context,opacity*[band[@"opacity"] doubleValue]);CGContextFillRect(context,CGRectMake(at,0,w,self.bounds.size.height));}at+=w;}}
                for(CGFloat y=0;y<self.bounds.size.height;y+=period){CGFloat at=y;for(NSDictionary *band in bands){CGFloat h=MAX(0,[band[@"width"] doubleValue]);if(!BNIsNull(band[@"color"])){CGContextSetFillColorWithColor(context,BNColorRef(band[@"color"],self).CGColor);CGContextSetAlpha(context,opacity*[band[@"opacity"] doubleValue]);CGContextFillRect(context,CGRectMake(0,at,self.bounds.size.width,h));}at+=h;}}
                if([pattern[@"twill"] boolValue]){CGContextSetAlpha(context,opacity*0.05);CGContextSetStrokeColorWithColor(context,BNRole(@"text.primary").CGColor);CGContextSetLineWidth(context,0.5);for(CGFloat start=-self.bounds.size.height;start<self.bounds.size.width;start+=3){CGContextMoveToPoint(context,start,self.bounds.size.height);CGContextAddLineToPoint(context,start+self.bounds.size.height,0);}CGContextStrokePath(context);}}
        }
        BNColor *fillColor=fill.length ? BNRole(fill) : nil;if([kind isEqual:@"Shape"]){NSString *source=BNSourceURL([_host prop:element name:@"fill_from" locals:_locals]);BNColor *average=source.length ? BNPictureAverage(_host,source) : nil;if(average)fillColor=average;if(!fillColor && !stroke.length)fillColor=BNRole(@"fill.strong");}
        if(fillColor){NSString *fade=BNPropString(_host,element,@"fade",_locals);if(fade.length){CGRect rect=CGPathGetBoundingBox(path);CGPoint start=CGPointMake(CGRectGetMidX(rect),CGRectGetMinY(rect)),end=CGPointMake(CGRectGetMidX(rect),CGRectGetMaxY(rect));if([fade isEqual:@"up"]){CGPoint swap=start;start=end;end=swap;}else if([fade isEqual:@"left"]){start=CGPointMake(CGRectGetMaxX(rect),CGRectGetMidY(rect));end=CGPointMake(CGRectGetMinX(rect),CGRectGetMidY(rect));}else if([fade isEqual:@"right"]){start=CGPointMake(CGRectGetMinX(rect),CGRectGetMidY(rect));end=CGPointMake(CGRectGetMaxX(rect),CGRectGetMidY(rect));}CGColorSpaceRef space=CGColorSpaceCreateDeviceRGB();CGGradientRef gradient=CGGradientCreateWithColors(space,(__bridge CFArrayRef)@[(__bridge id)fillColor.CGColor,(__bridge id)[fillColor colorWithAlphaComponent:0].CGColor],NULL);CGColorSpaceRelease(space);CGContextSaveGState(context);CGContextAddPath(context,path);CGContextClip(context);CGContextDrawLinearGradient(context,gradient,start,end,0);CGGradientRelease(gradient);CGContextRestoreGState(context);}else{CGContextAddPath(context,path);CGContextSetFillColorWithColor(context,fillColor.CGColor);CGContextFillPath(context);}}
        if(stroke.length){CGContextAddPath(context,strokePath ?: path);CGContextSetStrokeColorWithColor(context,BNRole(stroke).CGColor);CGContextSetLineWidth(context,BNPropNumber(_host,element,@"stroke_width",_locals,[kind isEqual:@"Series"] ? 2 : 1));CGContextSetLineCap(context,kCGLineCapRound);CGContextSetLineJoin(context,kCGLineJoinRound);CGFloat dash=BNPropNumber(_host,element,@"dash",_locals,0);if(dash>0){CGFloat pattern[]={dash,BNPropNumber(_host,element,@"dash_gap",_locals,dash)};CGContextSetLineDash(context,0,pattern,2);}CGContextStrokePath(context);}
        if(strokePath)CGPathRelease(strokePath);CGPathRelease(path);CGContextRestoreGState(context);
    }
}
@end

static NSDictionary *BNResolvedStyle(BNHost *host, NSDictionary *element, NSDictionary *locals) {
    NSString *kind=BNString(element[@"kind"]),*variant=BNPropString(host,element,@"variant",locals);
#if TARGET_OS_OSX
    NSString *platform=@"macos";
#else
    NSString *platform=@"ios";
#endif
    NSMutableArray *ordered=[NSMutableArray array];NSArray *rules=BNArray(BNDict(host.model[@"style"])[@"rules"]);
    for(NSUInteger phase=0;phase<2;phase++)for(NSDictionary *rule in rules){BOOL named=!BNIsNull(rule[@"variant"]);if(named!=(phase==1))continue;NSArray *targets=BNArray(rule[@"targets"]);if(![rule[@"component"] isEqual:kind] || (targets.count && ![targets containsObject:platform]) || [BNArray(rule[@"exempt"]) containsObject:platform])continue;if(named && ![rule[@"variant"] isEqual:variant])continue;[ordered addObject:rule];}
    NSMutableDictionary *base=[NSMutableDictionary dictionary],*states=[NSMutableDictionary dictionary];NSString *settle=@"";
    for(NSDictionary *rule in ordered){for(NSDictionary *effect in BNArray(rule[@"base"])){NSString *key=[effect[@"kind"] isEqual:@"metric"] ? BNString(effect[@"metric"]) : BNString(effect[@"kind"]);base[key]=effect;}for(NSDictionary *state in BNArray(rule[@"states"]))states[state[@"state"]]=BNArray(state[@"effects"]);if(!BNIsNull(rule[@"settle"]))settle=rule[@"settle"];}
    return @{@"base":base,@"states":states,@"settle":settle};
}
static void BNTintOnly(BNView *view, BNColor *color) {
#if TARGET_OS_OSX
    if([view respondsToSelector:@selector(setTextColor:)])[(id)view setTextColor:color];
    if([view isKindOfClass:NSButton.class])[(NSButton *)view setContentTintColor:color];
#else
    if([view respondsToSelector:@selector(setTextColor:)])[(id)view setTextColor:color];if([view isKindOfClass:UIButton.class])[(UIButton *)view setTitleColor:color forState:UIControlStateNormal];view.tintColor=color;
#endif
    if([view isKindOfClass:BNLayout.class])for(BNView *child in view.subviews)BNTintOnly(child,color);
}
static void BNForeground(BNView *view, BNColor *color) {
    NSMutableDictionary *meta=[BNMeta(view) mutableCopy];if(!meta[@"originalForeground"]){BNColor *original=nil;
#if TARGET_OS_OSX
        if([view respondsToSelector:@selector(textColor)])original=[(id)view textColor];else if([view isKindOfClass:NSButton.class])original=[(NSButton *)view contentTintColor];
#else
        if([view respondsToSelector:@selector(textColor)])original=[(id)view textColor];else if([view isKindOfClass:UIButton.class])original=[(UIButton *)view titleColorForState:UIControlStateNormal];
#endif
        meta[@"originalForeground"]=original ?: BNRole(@"text.primary");BNSetMeta(view,meta);
    }if([view isKindOfClass:BNLayout.class]){for(BNView *child in view.subviews)BNForeground(child,color);}else BNTintOnly(view,color);
}
static void BNRestoreForeground(BNView *view) {BNColor *color=BNMeta(view)[@"originalForeground"];if(color)BNTintOnly(view,color);if([view isKindOfClass:BNLayout.class])for(BNView *child in view.subviews)BNRestoreForeground(child);}
static void BNApplyStyle(BNHost *host, BNView *view, NSDictionary *element, NSDictionary *locals, BOOL selected) {
    NSDictionary *style=BNResolvedStyle(host,element,locals),*states=BNDict(style[@"states"]);NSMutableDictionary *effects=[BNDict(style[@"base"]) mutableCopy];NSString *interaction=BNString(BNMeta(view)[@"interactionState"]);
    if(!effects.count && !states.count)return;
    NSMutableArray *active=[NSMutableArray array];if(selected)[active addObject:@"selected"];if(interaction.length)[active addObject:interaction];if(!BNPropBool(host,element,@"enabled",locals,YES))[active addObject:@"disabled"];
    for(NSString *state in active)for(NSDictionary *effect in BNArray(states[state])){NSString *key=[effect[@"kind"] isEqual:@"metric"] ? BNString(effect[@"metric"]) : BNString(effect[@"kind"]);effects[key]=effect;}
    CALayer *layer=BNLayer(view);NSDictionary *initial=BNDict(BNMeta(view)[@"styleInitial"]);
    if(!initial.count){NSMutableDictionary *meta=[BNMeta(view) mutableCopy];meta[@"styleInitial"]=@{@"background":layer.backgroundColor ? (__bridge id)layer.backgroundColor : BNNull(),@"corner":@(layer.cornerRadius)};BNSetMeta(view,meta);initial=meta[@"styleInitial"];}
    layer.backgroundColor=BNIsNull(initial[@"background"]) ? NULL : (__bridge CGColorRef)initial[@"background"];layer.borderWidth=0;layer.opacity=1;layer.shadowOpacity=0;layer.cornerRadius=[initial[@"corner"] doubleValue];layer.transform=CATransform3DIdentity;
    BNRestoreForeground(view);CGFloat sx=1,sy=1,dx=0,dy=0;
    NSMutableDictionary *decoration=[BNMeta(view) mutableCopy];[decoration removeObjectForKey:@"styleIndicator"];
    for(NSString *effectKey in @[@"background",@"fill",@"foreground",@"border",@"corner",@"padding",@"size",@"shadow",@"opacity",@"scale",@"offset",@"indicator"]){NSDictionary *effect=effects[effectKey];if(!effect)continue;NSString *name=effect[@"kind"];
        if([name isEqual:@"background"] || ([name isEqual:@"fill"] && selected)){BNColor *color=BNColorRef(effect[@"color"],view);if([view isKindOfClass:BNScroll.class] && [element[@"kind"] isEqual:@"Form"]){BNScroll *form=(BNScroll *)view;for(BNView *section in form.document.subviews){NSDictionary *sectionMeta=BNMeta(section),*sectionElement=BNDict(sectionMeta[@"element"]);BOOL plain=[BNPropString(host,sectionElement,@"style",BNDict(sectionMeta[@"locals"])) isEqual:@"plain"];if(plain)continue;NSArray *rows=[section isKindOfClass:BNLayout.class] ? section.subviews : @[section];for(BNView *row in rows){if([BNMeta(row)[@"sectionAnnotation"] boolValue])continue;BNLayer(row).backgroundColor=color.CGColor;BNLayer(row).cornerRadius=6;}}}else layer.backgroundColor=color.CGColor;if([name isEqual:@"fill"])BNForeground(view,BNRole(@"on_accent"));}
        else if([name isEqual:@"border"]){layer.borderColor=BNColorRef(effect[@"color"],view).CGColor;layer.borderWidth=[effect[@"width"] doubleValue];}
        else if([name isEqual:@"corner"])layer.cornerRadius=[effect[@"radius"] doubleValue];
        else if([name isEqual:@"opacity"])layer.opacity=[effect[@"value"] floatValue];
        else if([name isEqual:@"shadow"]){layer.shadowColor=BNColor.blackColor.CGColor;layer.shadowOpacity=[effect[@"opacity"] floatValue];layer.shadowRadius=[effect[@"radius"] doubleValue];layer.shadowOffset=CGSizeMake(0,[effect[@"y"] doubleValue]);}
        else if([name isEqual:@"foreground"])BNForeground(view,BNColorRef(effect[@"color"],view));
        else if([name isEqual:@"scale"]){sx=[effect[@"x"] doubleValue];sy=[effect[@"y"] doubleValue];}
        else if([name isEqual:@"offset"]){dx=[effect[@"x"] doubleValue];dy=[effect[@"y"] doubleValue];}
        else if([name isEqual:@"indicator"])decoration[@"styleIndicator"]=@{@"color":(__bridge id)BNColorRef(effect[@"color"],view).CGColor,@"edge":effect[@"edge"],@"width":effect[@"width"]};
        else if([name isEqual:@"padding"]){CGFloat padding=[effect[@"length"] doubleValue];if([view isKindOfClass:BNLayout.class])[(BNLayout *)view setPadding:padding];
#if TARGET_OS_OSX
            else if([view isKindOfClass:BNStyledButton.class]){[(BNStyledButton *)view setBernPadding:padding];[view invalidateIntrinsicContentSize];}
#else
            else if([view isKindOfClass:UIButton.class])[(UIButton *)view setContentEdgeInsets:UIEdgeInsetsMake(padding,padding,padding,padding)];
#endif
        }
        else if([name isEqual:@"size"]){NSString *size=effect[@"size"];
#if TARGET_OS_OSX
            if([view isKindOfClass:NSControl.class])[(NSControl *)view setControlSize:[size isEqual:@"small"] ? NSControlSizeSmall : [size isEqual:@"regular"] ? NSControlSizeRegular : NSControlSizeLarge];
#else
            if([view isKindOfClass:UIButton.class]){CGFloat amount=[size isEqual:@"small"] ? 3 : [size isEqual:@"regular"] ? 6 : 10;[(UIButton *)view setContentEdgeInsets:UIEdgeInsetsMake(amount,amount*2,amount,amount*2)];}
#endif
        }
    }
    BNSetMeta(view,decoration);BNDecorations(view);
#if TARGET_OS_OSX
    if([view isKindOfClass:NSControl.class]){BOOL noRing=NO;for(NSDictionary *effect in BNArray(states[@"focus"]))if([effect[@"kind"] isEqual:@"nothing"])noRing=YES;[(NSControl *)view setFocusRingType:noRing ? NSFocusRingTypeNone : NSFocusRingTypeDefault];if([view isKindOfClass:BNStyledButton.class] && (effects[@"background"] || effects[@"border"] || effects[@"corner"]))[(NSButton *)view setBordered:NO];}
#endif
    layer.transform=CATransform3DTranslate(CATransform3DMakeScale(sx,sy,1),dx,dy,0);
    NSMutableDictionary *motionMeta=[BNMeta(view) mutableCopy];motionMeta[@"styleTransform"]=[NSValue valueWithCATransform3D:layer.transform];motionMeta[@"styleOpacity"]=@(layer.opacity);BNSetMeta(view,motionMeta);
    if([view isKindOfClass:BNStyledButton.class]){__weak BNView *weakView=view;__weak BNHost *weakHost=host;void(^feedback)(NSString *)=^(NSString *state){BNView *target=weakView;if(!target)return;NSMutableDictionary *meta=[BNMeta(target) mutableCopy];meta[@"interactionState"]=state;BNSetMeta(target,meta);[CATransaction begin];[CATransaction setAnimationDuration:0.12];BNApplyStyle(weakHost,target,element,locals,selected);[CATransaction commit];};[(BNStyledButton *)view setFeedback:feedback];}
}

@implementation BNHost (Rendering)
-(BNView *)renderElement:(NSDictionary *)element locals:(NSDictionary *)locals {
    NSString *kind=BNString(element[@"kind"]),*label=BNPropString(self,element,@"label",locals),*icon=BNPropString(self,element,@"icon",locals);
    if([kind isEqual:@"Stack"] && !BNPropBool(self,element,@"enabled",locals,YES)){NSMutableDictionary *inner=[locals mutableCopy];inner[@"__disabled"]=@YES;locals=inner;}
    NSDictionary *props=BNDict(element[@"props"]);BNView *view=nil;BOOL selected=NO;
    CGFloat gap=BNPropNumber(self,element,@"gap",locals,8);
    if([kind isEqual:@"ForEach"]){BNLayout *column=BNContainer(@"column",0);column.fillWidth=YES;for(NSDictionary *descriptor in BNDescriptors(self,@[element],locals))[column addSubview:[self renderElement:descriptor[@"element"] locals:descriptor[@"locals"]]];view=column;}
    else if([kind isEqual:@"Text"]){view=BNLabel(self,BNPropString(self,element,@"content",locals),element,locals);}
    else if([kind isEqual:@"Label"]){BNLayout *row=BNContainer(@"row",5);NSString *title=BNPropString(self,element,@"title",locals);
#if TARGET_OS_OSX
        NSImageView *image=[[NSImageView alloc] initWithFrame:CGRectZero];image.image=[NSImage imageWithSystemSymbolName:icon accessibilityDescription:title];
#else
        UIImageView *image=[[UIImageView alloc] initWithImage:[UIImage systemImageNamed:icon]];image.contentMode=UIViewContentModeScaleAspectFit;
#endif
        BNSetMeta(image,@{@"minimumSize":@[@18,@18]});[row addSubview:image];if(![BNPropString(self,element,@"display",locals) isEqual:@"icon"])[row addSubview:BNLabel(self,title,element,locals)];view=row;
    }
    else if([@[@"Button",@"IconButton",@"MenuItem",@"SearchItem",@"NavLink",@"SidebarItem"] containsObject:kind]){
        BOOL sidebar=[kind isEqual:@"SidebarItem"],nav=[kind isEqual:@"NavLink"];
        NSDictionary *selection=locals[@"__selection"];id choice=[self prop:element name:sidebar ? @"value" : @"route" locals:locals];
        if(sidebar && selection)selected=[[self field:selection locals:locals] isEqual:choice];
        BNControl *control=[self registerControl:element view:nil role:sidebar ? @"sidebar_item" : nav ? @"navigation_link" : @"button" label:label locals:locals];
        __weak BNHost *weakHost=self;__block __weak BNView *weakView=nil;
        control.activate=^{BNHost *host=weakHost;if(!host || !BNPropBool(host,element,@"enabled",locals,YES))return;
            if(sidebar && selection){objc_setAssociatedObject(locals[@"__window"],BNSidebarShownKey,@NO,OBJC_ASSOCIATION_RETAIN_NONATOMIC);[host setField:selection value:choice locals:locals];}
            else if(nav && locals[@"__path"]){NSDictionary *path=locals[@"__path"];NSMutableArray *values=[BNArray([host field:path locals:locals]) mutableCopy];[values addObject:choice ?: BNNull()];[host setField:path value:values locals:locals];}
            else BNFire(host,element,locals,weakView);
        };
        BOOL plain=sidebar || [kind isEqual:@"SearchItem"] || [BNPropString(self,element,@"prominence",locals) isEqual:@"plain"];
        if(BNArray(element[@"children"]).count && !nav){BNStyledButton *button=(BNStyledButton *)BNMakeButton(@"",@"",control,plain);BNLayout *content=BNContainer(@"stack",0);content.alignment=@"center";for(BNView *child in BNRendered(self,element[@"children"],locals))[content addSubview:child];button.customContent=content;view=button;}
        else {NSString *title=[kind isEqual:@"IconButton"] ? @"" : label;
            if(nav && !title.length){BNStyledButton *button=(BNStyledButton *)BNMakeButton(@"",@"",control,YES);BNLayout *content=BNContainer(@"row",6);for(BNView *child in BNRendered(self,element[@"children"],locals))[content addSubview:child];button.customContent=content;view=button;}
            else view=BNMakeButton(title,icon,control,plain);
        }
        if(sidebar){BNStyledButton *button=(BNStyledButton *)BNMakeButton(label,icon,control,YES);
#if TARGET_OS_OSX
            button.alignment=NSTextAlignmentLeft;
#else
            button.contentHorizontalAlignment=UIControlContentHorizontalAlignmentLeft;
#endif
            CGFloat badge=BNPropNumber(self,element,@"badge",locals,0);if(badge>0){BNView *annotation=BNLabel(self,[@((NSInteger)badge) description],@{@"props":@{@"emphasis":@{@"kind":@"keyword",@"value":@"secondary"},@"style":@{@"kind":@"keyword",@"value":@"caption"}}},locals);
#if TARGET_OS_OSX
                ((NSTextField *)annotation).selectable=NO;
#else
                annotation.userInteractionEnabled=NO;
#endif
                button.badge=annotation;[button addSubview:annotation];}view=button;
        }
        weakView=view;control.view=view;BNInstallFileAction(self,control,element,locals,view);
        if(selected){BNLayer(view).backgroundColor=BNRole(@"selection.background").CGColor;BNLayer(view).cornerRadius=6;}
        if(sidebar)BNSetMeta(view,@{@"fillWidth":@YES,@"minimumSize":@[@0,@30]});
    }
    else if([kind isEqual:@"Menu"]){
        BNControl *control=[self registerControl:element view:nil role:@"menu" label:label locals:locals];
        NSMutableArray<BNControl *> *items=[NSMutableArray array];NSMutableArray *separators=[NSMutableArray array];
        for(NSDictionary *descriptor in BNDescriptors(self,element[@"children"],locals)){
            NSDictionary *node=descriptor[@"element"],*scope=descriptor[@"locals"];
            if([node[@"kind"] isEqual:@"Divider"]){[separators addObject:@(items.count)];continue;}
            if(![node[@"kind"] isEqual:@"MenuItem"])continue;
            BNView *item=[self renderElement:node locals:scope];(void)item;BNControl *entry=self.controls.lastObject;if(entry && entry!=control)[items addObject:entry];
        }
        view=BNMakeButton([BNPropString(self,element,@"style",locals) isEqual:@"icon"] ? @"" : label,icon,control,NO);control.view=view;__weak BNView *anchor=view;
#if TARGET_OS_OSX
        NSMenu *menu=[[NSMenu alloc] initWithTitle:label];menu.autoenablesItems=NO;for(NSUInteger i=0;i<items.count;i++){if([separators containsObject:@(i)])[menu addItem:NSMenuItem.separatorItem];BNControl *entry=items[i];NSMenuItem *item=[[NSMenuItem alloc] initWithTitle:entry.label action:@selector(clicked:) keyEquivalent:@""];item.target=entry;item.enabled=entry.enabled;NSString *symbol=BNPropString(self,entry.element,@"icon",entry.locals);if(symbol.length)item.image=[NSImage imageWithSystemSymbolName:symbol accessibilityDescription:entry.label];[menu addItem:item];}
        control.activate=^{BNView *source=anchor;if(source)[menu popUpMenuPositioningItem:nil atLocation:CGPointMake(0,source.bounds.size.height) inView:source];};
#else
        NSMutableArray *actions=[NSMutableArray array];for(BNControl *entry in items){UIAction *action=[UIAction actionWithTitle:entry.label image:[UIImage systemImageNamed:BNPropString(self,entry.element,@"icon",entry.locals)] identifier:nil handler:^(__kindof UIAction *action){@try{[entry.host performControl:entry event:@"activate" value:BNNull()];}@catch(NSException *error){[entry.host showError:error.reason];}}];if(!entry.enabled)action.attributes|=UIMenuElementAttributesDisabled;if([BNPropString(self,entry.element,@"role",entry.locals) isEqual:@"destructive"])action.attributes|=UIMenuElementAttributesDestructive;[actions addObject:action];}
        UIButton *button=(UIButton *)view;button.menu=[UIMenu menuWithTitle:@"" children:actions];button.showsMenuAsPrimaryAction=YES;
        control.activate=^{[anchor becomeFirstResponder];};
#endif
    }
    else if([kind isEqual:@"PopoverButton"] || [kind isEqual:@"SplitButton"]){
        BOOL split=[kind isEqual:@"SplitButton"];BNControl *control=[self registerControl:element view:nil role:split ? @"split_button" : @"popover_button" label:label locals:locals];
        view=BNMakeButton(label,icon,control,NO);control.view=view;__weak BNHost *host=self;__weak BNView *anchor=view;
        NSDictionary *presented=BNDict(props[@"presented"])[@"field"];
        control.activate=^{if(presented)[host setField:presented value:@YES locals:locals];else BNShowPopover(host,element,locals,anchor);};
        if(presented && BNPropBool(self,element,@"presented",locals,NO))dispatch_async(dispatch_get_main_queue(),^{BNShowPopover(host,element,locals,anchor);});else if(presented)BNDismissPopover(self,element,locals);control.value=^{return BNPopovers(host)[BNPopoverIdentity(element,locals)] ? @"open" : @"closed";};
        if(split){BNLayout *row=BNContainer(@"row",0);id current=BNControlValue(self,element,@"checked",locals);selected=[current respondsToSelector:@selector(boolValue)] && [current boolValue];control.setBool=^(BOOL next){BNSetControlValue(host,element,locals,@(next));};__weak BNControl *weakControl=control;control.activate=^{if(weakControl.setBool)weakControl.setBool(!selected);};
            BNControl *more=[self registerControl:element view:nil role:@"popover_button" label:BNPropString(self,element,@"more_label",locals) locals:locals];BNView *button=BNMakeButton(@"",@"chevron.down",more,NO);more.view=button;__weak BNView *moreAnchor=button;more.activate=^{BNShowPopover(host,element,locals,moreAnchor);};[row addSubview:view];[row addSubview:button];view=row;
        }
    }
    else if([kind isEqual:@"Timer"]){view=[[BNView alloc] initWithFrame:CGRectZero];BNInstallTimer(self,element,locals,view);}
    else if([kind isEqual:@"Shortcut"]){view=[[BNView alloc] initWithFrame:CGRectZero];BNControl *control=[self registerControl:element view:view role:@"shortcut" label:label locals:locals];__weak BNHost *host=self;__weak BNView *anchor=view;control.activate=^{BNFire(host,element,locals,anchor);};}
    else if([kind isEqual:@"Switch"]){id value=BNControlValue(self,element,@"checked",locals);BOOL on=[value respondsToSelector:@selector(boolValue)] && [value boolValue];selected=on;
        BNControl *control=[self registerControl:element view:nil role:@"switch" label:label locals:locals];__weak BNHost *weakHost=self;
        control.setBool=^(BOOL next){BNSetControlValue(weakHost,element,locals,@(next));};control.value=^{return [BNControlValue(weakHost,element,@"checked",locals) boolValue] ? @"true" : @"false";};__weak BNControl *weakControl=control;control.activate=^{if(weakControl.setBool)weakControl.setBool(![BNControlValue(weakHost,element,@"checked",locals) boolValue]);};
        NSString *toggleStyle=BNPropString(self,element,@"style",locals);BNView *toggle=nil;
        if([toggleStyle isEqual:@"button"]){toggle=BNMakeButton(BNPropBool(self,element,@"label_hidden",locals,NO) ? @"" : label,icon,control,YES);BNLayer(toggle).cornerRadius=15;BNLayer(toggle).backgroundColor=(on ? BNRole(@"accent") : BNRole(@"fill.subtle")).CGColor;if(on)BNTintOnly(toggle,BNRole(@"on_accent"));view=toggle;}
        else {
#if TARGET_OS_OSX
        if([toggleStyle isEqual:@"switch"]){NSSwitch *native=[[NSSwitch alloc] initWithFrame:CGRectZero];native.target=control;native.action=@selector(changed:);native.state=on ? NSControlStateValueOn : NSControlStateValueOff;toggle=native;if(BNPropBool(self,element,@"label_hidden",locals,NO))view=toggle;else{BNLayout *row=BNContainer(@"row",8);[row addSubview:BNLabel(self,label,element,locals)];[row addSubview:toggle];view=row;}}
        else{NSButton *native=[NSButton checkboxWithTitle:BNPropBool(self,element,@"label_hidden",locals,NO) ? @"" : label target:control action:@selector(changed:)];native.state=on ? NSControlStateValueOn : NSControlStateValueOff;toggle=native;view=toggle;}
#else
        UISwitch *native=[[UISwitch alloc] initWithFrame:CGRectZero];native.on=on;[native addTarget:control action:@selector(changed:) forControlEvents:UIControlEventValueChanged];toggle=native;
        if(BNPropBool(self,element,@"label_hidden",locals,NO))view=toggle;else{BNLayout *row=BNContainer(@"row",8);row.fillWidth=YES;[row addSubview:BNLabel(self,label,element,locals)];BNView *spacer=[[BNView alloc] initWithFrame:CGRectZero];BNSetMeta(spacer,@{@"kind":@"Spacer",@"grow":@YES});[row addSubview:spacer];[row addSubview:toggle];view=row;}
#endif
        }
        BNKeep(toggle,control);control.view=toggle;
    }
    else if([kind isEqual:@"Slider"]){double minimum=BNPropNumber(self,element,@"min",locals,0),maximum=BNPropNumber(self,element,@"max",locals,1),step=BNPropNumber(self,element,@"step",locals,0);
        id current=BNControlValue(self,element,@"current",locals);double value=[current respondsToSelector:@selector(doubleValue)] ? [current doubleValue] : minimum;
        BNControl *control=[self registerControl:element view:nil role:@"slider" label:label locals:locals];__weak BNHost *weakHost=self;
        control.setNumber=^(double next){next=MAX(minimum,MIN(maximum,next));if(step>0)next=minimum+round((next-minimum)/step)*step;BNSetControlValue(weakHost,element,locals,@(next));};control.value=^{return BNString(BNControlValue(weakHost,element,@"current",locals));};
#if TARGET_OS_OSX
        BNTrackingSlider *slider=[BNTrackingSlider sliderWithValue:value minValue:minimum maxValue:maximum target:control action:@selector(changed:)];slider.continuous=YES;
#else
        UISlider *slider=[[UISlider alloc] initWithFrame:CGRectZero];slider.minimumValue=minimum;slider.maximumValue=maximum;slider.value=value;[slider addTarget:control action:@selector(changed:) forControlEvents:UIControlEventValueChanged];[slider addTarget:control action:@selector(beganTracking:) forControlEvents:UIControlEventTouchDown];[slider addTarget:control action:@selector(endedTracking:) forControlEvents:UIControlEventTouchUpInside|UIControlEventTouchUpOutside|UIControlEventTouchCancel];
#endif
        BNSetMeta(slider,@{@"fillWidth":@YES,@"minimumSize":@[@140,@28]});BNKeep(slider,control);control.view=slider;
        if(BNPropBool(self,element,@"label_hidden",locals,NO))view=slider;else{BNLayout *column=BNContainer(@"column",4);column.fillWidth=YES;[column addSubview:BNLabel(self,label,element,locals)];[column addSubview:slider];view=column;}
    }
    else if([kind isEqual:@"Search"]){view=BNRenderSearch(self,element,locals);}
    else if([kind isEqual:@"TextInput"]){BOOL search=[kind isEqual:@"Search"],secure=[BNPropString(self,element,@"kind",locals) isEqual:@"secure"],multiline=[BNPropString(self,element,@"kind",locals) isEqual:@"multiline"];
        NSString *current=BNString(BNControlValue(self,element,@"current",locals));NSString *prompt=BNPropString(self,element,@"prompt",locals);
        BNControl *control=[self registerControl:element view:nil role:search ? @"search" : @"text_input" label:label.length ? label : prompt locals:locals];__weak BNHost *weakHost=self;__block __weak BNView *weakView=nil;
        NSDictionary *field=BNDict(props[@"value"])[@"field"];
        control.edit=^(NSString *text){if(field)[weakHost setField:field value:text locals:locals];};
        control.submit=^{BNFire(weakHost,element,locals,weakView);};if(!secure)control.value=^{return BNString(BNControlValue(weakHost,element,@"current",locals));};
        BNFieldDelegate *delegate=[BNFieldDelegate new];delegate.control=control;
#if TARGET_OS_OSX
        if(multiline){NSTextView *text=[[NSTextView alloc] initWithFrame:CGRectZero];text.string=current;text.font=BNTextFont(self,element,locals);text.delegate=delegate;view=text;}
        else {NSTextField *text=search ? [[NSSearchField alloc] initWithFrame:CGRectZero] : secure ? [[NSSecureTextField alloc] initWithFrame:CGRectZero] : [[NSTextField alloc] initWithFrame:CGRectZero];text.stringValue=current;text.placeholderString=prompt;text.font=BNTextFont(self,element,locals);text.delegate=delegate;text.target=control;text.action=@selector(submitted:);view=text;}
#else
        if(multiline){UITextView *text=[[UITextView alloc] initWithFrame:CGRectZero];text.text=current;text.font=BNTextFont(self,element,locals);text.delegate=delegate;view=text;}
        else {UITextField *text=search ? [[UISearchTextField alloc] initWithFrame:CGRectZero] : [[UITextField alloc] initWithFrame:CGRectZero];text.text=current;text.placeholder=prompt;text.secureTextEntry=secure;text.borderStyle=UITextBorderStyleRoundedRect;text.font=BNTextFont(self,element,locals);text.delegate=delegate;text.returnKeyType=search ? UIReturnKeySearch : UIReturnKeyDone;[text addTarget:control action:@selector(changed:) forControlEvents:UIControlEventEditingChanged];view=text;}
#endif
        weakView=view;control.view=view;BNKeep(view,delegate);BNSetMeta(view,@{@"fillWidth":@YES,@"minimumSize":@[@160,@(multiline ? 90 : 30)]});
        control.focus=^{
#if TARGET_OS_OSX
            [weakView.window makeFirstResponder:weakView];
#else
            [weakView becomeFirstResponder];
#endif
        };
        if(!search && !BNPropBool(self,element,@"label_hidden",locals,NO)){BNLayout *column=BNContainer(@"column",4);column.fillWidth=YES;[column addSubview:BNLabel(self,label,element,locals)];[column addSubview:view];view=column;}
        if(search && BNArray(element[@"children"]).count){BNLayout *column=BNContainer(@"column",6);column.fillWidth=YES;[column addSubview:view];if(current.length)for(BNView *child in BNRendered(self,element[@"children"],locals))[column addSubview:child];view=column;}
    }
    else if([kind isEqual:@"Picker"] || [kind isEqual:@"LanguagePicker"]){BOOL language=[kind isEqual:@"LanguagePicker"];NSMutableArray *titles=[NSMutableArray array],*values=[NSMutableArray array],*names=[NSMutableArray array];
        id current=language ? self.language : BNControlValue(self,element,@"selected",locals);NSDictionary *field=BNDict(props[@"value"])[@"field"],*type=BNDict(field[@"type"] ?: BNDict(BNDict(props[@"selected"])[@"expr"])[@"type"]);
        if(language){for(NSString *code in BNArray(BNDict(self.model[@"languages"])[@"supported"])){[titles addObject:[[NSLocale localeWithLocaleIdentifier:code] localizedStringForLanguageCode:code] ?: code];[values addObject:code];[names addObject:code];}}
        else {for(NSDictionary *descriptor in BNDescriptors(self,element[@"children"],locals)){NSDictionary *node=descriptor[@"element"],*scope=descriptor[@"locals"];if(![node[@"kind"] isEqual:@"PickerOption"])continue;id value=[self prop:node name:@"value" locals:scope];[values addObject:value ?: BNNull()];[titles addObject:BNPropString(self,node,@"label",scope)];NSDictionary *definition=[self typeNamed:BNString(type[@"name"]) list:@"enums"];NSUInteger index=[BNDict(value)[@"variant"] unsignedIntegerValue];[names addObject:BNString(BNDict(BNAt(BNArray(definition[@"variants"]),index))[@"name"])];}
            if(!values.count){NSDictionary *definition=[self typeNamed:BNString(type[@"name"]) list:@"enums"];NSUInteger index=0;for(NSDictionary *variant in BNArray(definition[@"variants"])){NSDictionary *value=@{@"variant":@(index++),@"fields":@[]};[values addObject:value];[names addObject:BNString(variant[@"name"])];[titles addObject:[self display:value type:type]];}}
        }
        NSUInteger selectedIndex=[values indexOfObject:current];if(selectedIndex==NSNotFound)selectedIndex=0;
        BNControl *control=[self registerControl:element view:nil role:@"picker" label:label locals:locals];__weak BNHost *weakHost=self;
        control.select=^BOOL(NSString *name){NSUInteger index=[names indexOfObject:name];if(index==NSNotFound)index=[titles indexOfObject:name];if(index==NSNotFound){NSInteger n=[name integerValue];if([name isEqual:[@(n) description]] && n>=0 && (NSUInteger)n<values.count)index=n;}if(index==NSNotFound)return NO;if(language){weakHost.language=values[index];[weakHost scheduleRender];}else BNSetControlValue(weakHost,element,locals,values[index]);return YES;};
        control.value=^{return selectedIndex<names.count ? names[selectedIndex] : @"";};
        BOOL segmented=[BNPropString(self,element,@"style",locals) isEqual:@"segmented"];
        NSString *pickerStyle=BNPropString(self,element,@"style",locals);BOOL custom=[@[@"radio",@"inline",@"chips"] containsObject:pickerStyle];
        if(custom){BNLayout *options=BNContainer([pickerStyle isEqual:@"chips"] ? @"flow" : @"column",[pickerStyle isEqual:@"chips"] ? 8 : 4);__weak BNControl *weakPicker=control;for(NSUInteger i=0;i<titles.count;i++){NSUInteger index=i;NSMutableDictionary *option=[element mutableCopy];option[@"id"]=[NSString stringWithFormat:@"%@.%@",BNString(element[@"id"]),names[i]];option[@"path"]=[NSString stringWithFormat:@"%@.%lu",BNString(element[@"path"]),(unsigned long)i];BNControl *entry=[self registerControl:option view:nil role:@"picker_option" label:titles[i] locals:locals];entry.activate=^{if(weakPicker.select)weakPicker.select(names[index]);};NSString *symbol=[pickerStyle isEqual:@"radio"] ? (i==selectedIndex ? @"largecircle.fill.circle" : @"circle") : [pickerStyle isEqual:@"inline"] && i==selectedIndex ? @"checkmark" : @"";BNView *button=BNMakeButton(titles[i],symbol,entry,YES);entry.view=button;if([pickerStyle isEqual:@"chips"]){BNLayer(button).cornerRadius=15;BNLayer(button).backgroundColor=(i==selectedIndex ? BNRole(@"accent") : BNRole(@"fill.subtle")).CGColor;if(i==selectedIndex)BNTintOnly(button,BNRole(@"on_accent"));BNSetMeta(button,@{@"minimumSize":@[@0,@30]});}[options addSubview:button];}view=options;}
        else {
#if TARGET_OS_OSX
        if(segmented){NSSegmentedControl *picker=[NSSegmentedControl segmentedControlWithLabels:titles trackingMode:NSSegmentSwitchTrackingSelectOne target:control action:@selector(changed:)];picker.selectedSegment=selectedIndex;view=picker;}
        else{NSPopUpButton *picker=[[NSPopUpButton alloc] initWithFrame:CGRectZero pullsDown:NO];[picker addItemsWithTitles:titles];for(NSUInteger i=0;i<picker.numberOfItems;i++)[picker itemAtIndex:i].representedObject=names[i];if(titles.count)[picker selectItemAtIndex:selectedIndex];picker.target=control;picker.action=@selector(changed:);view=picker;}
#else
        if(segmented){UISegmentedControl *picker=[[UISegmentedControl alloc] initWithItems:titles];picker.selectedSegmentIndex=selectedIndex;[picker addTarget:control action:@selector(changed:) forControlEvents:UIControlEventValueChanged];view=picker;}
        else{UIButton *picker=[UIButton buttonWithType:UIButtonTypeSystem];[picker setTitle:selectedIndex<titles.count ? titles[selectedIndex] : label forState:UIControlStateNormal];NSMutableArray *actions=[NSMutableArray array];for(NSUInteger i=0;i<titles.count;i++){NSUInteger index=i;UIAction *action=[UIAction actionWithTitle:titles[i] image:nil identifier:nil handler:^(__kindof UIAction *a){control.select(names[index]);}];action.state=i==selectedIndex ? UIMenuElementStateOn : UIMenuElementStateOff;[actions addObject:action];}picker.menu=[UIMenu menuWithTitle:label children:actions];picker.showsMenuAsPrimaryAction=YES;view=picker;}
#endif
        }
        control.view=view;BNKeep(view,control);BNSetMeta(view,@{@"minimumSize":@[@100,@30]});
        if(!BNPropBool(self,element,@"label_hidden",locals,NO) && label.length){BNLayout *row=BNContainer(@"row",8);[row addSubview:BNLabel(self,label,element,locals)];[row addSubview:view];view=row;}
    }
    else if([kind isEqual:@"Image"]){NSString *source=BNSourceURL([self prop:element name:@"source" locals:locals]);if(!source.length)source=BNPropString(self,element,@"name",locals);BNPictureView *picture=[[BNPictureView alloc] initWithFrame:CGRectZero];picture.image=BNLoadPicture(self,source);picture.fit=BNPropString(self,element,@"fit",locals);picture.templateImage=[BNPropString(self,element,@"rendering",locals) isEqual:@"template"];view=picture;BNLayer(view).cornerRadius=BNPropNumber(self,element,@"corner",locals,0);BNLayer(view).masksToBounds=YES;CGSize natural=picture.intrinsicContentSize;BNSetMeta(view,@{@"pictureAspect":@(BNPropNumber(self,element,@"aspect",locals,natural.height>0 ? natural.width/natural.height : 1))});}
    else if([kind isEqual:@"Video"]){if(!label.length)label=BNMediaText(@"bern.media.video");BNWindow *window=locals[@"__window"];BNControl *control=[self registerControl:element view:nil role:@"video" label:label locals:locals];NSString *player=BNPropString(self,element,@"player",locals),*token=[NSString stringWithFormat:@"%@/%@",window.identifier,control.target];if(!player.length){player=token;BNMediaBind(player,window.identifier,BNSourceURL([self prop:element name:@"source" locals:locals]));}BNView *surface=BNMediaVideo(player,token,window.identifier,BNPropString(self,element,@"fit",locals),BNPropNumber(self,element,@"corner",locals,0));control.view=surface;control.value=^{return BNMediaDescription(player);};BNSetMeta(surface,@{@"fillWidth":@YES,@"pictureAspect":@(16.0/9.0),@"minimumSize":@[@320,@180]});if([BNPropString(self,element,@"controls",locals) isEqual:@"none"])view=surface;else{BNLayout *column=BNContainer(@"column",6);column.fillWidth=YES;[column addSubview:surface];[column addSubview:BNMediaControls(player,control.target,locals)];view=column;}}
    else if([kind isEqual:@"Progress"]){id value=[self prop:element name:@"value" locals:locals];CGFloat total=MAX(0.00001,BNPropNumber(self,element,@"total",locals,1));
#if TARGET_OS_OSX
        NSProgressIndicator *progress=[[NSProgressIndicator alloc] initWithFrame:CGRectZero];progress.indeterminate=BNIsNull(value);progress.style=BNIsNull(value) ? NSProgressIndicatorStyleSpinning : NSProgressIndicatorStyleBar;progress.minValue=0;progress.maxValue=total;if(!BNIsNull(value))progress.doubleValue=[value doubleValue];else[progress startAnimation:nil];view=progress;
#else
        if(BNIsNull(value)){UIActivityIndicatorView *progress=[[UIActivityIndicatorView alloc] initWithActivityIndicatorStyle:UIActivityIndicatorViewStyleMedium];[progress startAnimating];view=progress;}else{UIProgressView *progress=[[UIProgressView alloc] initWithProgressViewStyle:UIProgressViewStyleDefault];progress.progress=[value floatValue]/total;view=progress;}
#endif
        BNSetMeta(view,@{@"fillWidth":@(!BNIsNull(value)),@"minimumSize":@[@(BNIsNull(value) ? 20 : 100),@20]});
    }
    else if([kind isEqual:@"Canvas"]){BNCanvasView *canvas=[[BNCanvasView alloc] initWithFrame:CGRectZero];canvas.host=self;canvas.drawings=BNArray(element[@"children"]);canvas.locals=locals;view=canvas;BNSetMeta(view,@{@"minimumSize":@[@100,@100],@"fills":@YES});}
    else if([kind isEqual:@"Divider"]){view=[[BNView alloc] initWithFrame:CGRectZero];BNLayer(view).backgroundColor=BNRole(@"control.border").CGColor;BNSetMeta(view,@{@"fillWidth":@YES,@"minimumSize":@[@1,@1]});}
    else if([kind isEqual:@"Spacer"]){view=[[BNView alloc] initWithFrame:CGRectZero];BNSetMeta(view,@{@"kind":@"Spacer",@"grow":@YES});}
    else if([kind isEqual:@"WindowButtons"]){view=[[BNView alloc] initWithFrame:CGRectZero];
#if TARGET_OS_OSX
        BNSetMeta(view,@{@"minimumSize":@[@70,@26]});
#endif
    }
    else if([kind isEqual:@"ScrollView"] || [kind isEqual:@"Form"] || [kind isEqual:@"List"]){BNScroll *scroll=[[BNScroll alloc] initWithFrame:CGRectZero];scroll.host=self;scroll.element=element;scroll.locals=locals;scroll.horizontal=[BNPropString(self,element,@"axis",locals) isEqual:@"horizontal"];scroll.indicators=![BNPropString(self,element,@"indicators",locals) isEqual:@"hidden"];scroll.openAt=BNPropNumber(self,element,@"open_at",locals,0);BNLayout *document=BNContainer(scroll.horizontal ? @"row" : @"column",[kind isEqual:@"Form"] ? BNPropNumber(self,element,@"gap",locals,20) : gap);document.fillWidth=!scroll.horizontal;NSArray *body=BNArray(element[@"children"]);if([kind isEqual:@"List"] && !BNIsNull(props[@"items"])) {NSMutableDictionary *each=[element mutableCopy];each[@"kind"]=@"ForEach";body=@[each];}for(BNView *child in BNRendered(self,body,locals))[document addSubview:child];scroll.document=document;if([kind isEqual:@"Form"])BNConfigureForm(self,scroll,element,locals);view=scroll;BNSetMeta(view,@{@"fillWidth":@YES});}
    else if([kind isEqual:@"SplitView"]){
        BNWindow *window=locals[@"__window"];BOOL compact=window.root.bounds.size.width>0 && window.root.bounds.size.width<600;
        BNLayout *split=BNContainer(@"split",1);split.fillWidth=YES;split.fillHeight=YES;NSMutableDictionary *meta=[NSMutableDictionary dictionaryWithObject:@210 forKey:@"sidebar"];meta[@"showSidebar"]=objc_getAssociatedObject(window,BNSidebarShownKey) ?: @NO;
        for(NSDictionary *descriptor in BNDescriptors(self,element[@"children"],locals)){NSDictionary *node=descriptor[@"element"],*scope=descriptor[@"locals"];BNView *child=[self renderElement:node locals:scope];if([node[@"kind"] isEqual:@"Sidebar"])meta[@"sidebar"]=@(BNPropNumber(self,node,@"width",scope,210));
            if(compact && [node[@"kind"] isEqual:@"Detail"]){BNLayout *detail=BNContainer(@"column",6);detail.fillWidth=YES;detail.fillHeight=YES;NSDictionary *toggle=@{@"kind":@"Button",@"id":@"bern_sidebar_toggle",@"path":@"bern_sidebar_toggle",@"props":@{}};BNControl *control=[self registerControl:toggle view:nil role:@"button" label:@"Sidebar" locals:locals];__weak BNHost *host=self;control.activate=^{objc_setAssociatedObject(window,BNSidebarShownKey,@YES,OBJC_ASSOCIATION_RETAIN_NONATOMIC);[host scheduleRender];};BNView *button=BNMakeButton(@"Sidebar",@"sidebar.left",control,YES);control.view=button;[detail addSubview:button];[detail addSubview:child];child=detail;}
            [split addSubview:child];
        }BNSetMeta(split,meta);view=split;
    }
    else if([kind isEqual:@"Sidebar"]){NSDictionary *field=BNDict(props[@"selection"])[@"field"];NSMutableDictionary *inner=[locals mutableCopy];if(field)inner[@"__selection"]=field;BNLayout *column=BNContainer(@"column",4);column.fillWidth=YES;column.fillHeight=YES;column.paddingX=8;column.paddingY=10;for(BNView *child in BNRendered(self,element[@"children"],inner))[column addSubview:child];BNLayer(column).backgroundColor=BNRole(@"surface.panel").CGColor;view=column;
        if(!BNIsNull(element[@"id"])){BNControl *control=[self registerControl:element view:view role:@"sidebar" label:label locals:locals];__weak BNHost *host=self;NSDictionary *type=BNDict(field[@"type"]);NSDictionary *definition=[self typeNamed:BNString(type[@"name"]) list:@"enums"];control.select=^BOOL(NSString *name){NSUInteger index=0;for(NSDictionary *variant in BNArray(definition[@"variants"])){if([variant[@"name"] isEqual:name])return [host setField:field value:@{@"variant":@(index),@"fields":@[]} locals:locals];index++;}return NO;};control.value=^{return [host display:[host field:field locals:locals] type:type];};}
    }
    else if([kind isEqual:@"Navigation"]){
#if TARGET_OS_OSX
        NSDictionary *field=BNDict(props[@"path"])[@"field"];NSArray *path=BNArray([self field:field locals:locals]);NSMutableDictionary *inner=[locals mutableCopy];if(field)inner[@"__path"]=field;BNLayout *column=BNContainer(@"column",8);column.fillWidth=YES;column.fillHeight=YES;
        if(path.count){NSString *backTitle=[self frameworkText:@"bern.navigation.back" fallback:@"Back"];BNControl *back=[self registerControl:element view:nil role:@"navigation" label:backTitle locals:locals];__weak BNHost *host=self;back.back=^BOOL{NSMutableArray *values=[BNArray([host field:field locals:locals]) mutableCopy];if(!values.count)return NO;[values removeLastObject];return [host setField:field value:values locals:locals];};__weak BNControl *weakBack=back;back.activate=^{if(weakBack.back)weakBack.back();};BNView *button=BNMakeButton(backTitle,@"chevron.left",back,YES);back.view=button;[column addSubview:button];
            for(NSDictionary *descriptor in BNDescriptors(self,element[@"children"],inner)){NSDictionary *node=descriptor[@"element"];if(![node[@"kind"] isEqual:@"Destination"])continue;NSMutableDictionary *scope=[descriptor[@"locals"] mutableCopy];NSDictionary *template=BNDict(node[@"template"]);if(template[@"var"])scope[template[@"var"]]=path.lastObject;for(BNView *child in BNRendered(self,node[@"children"],scope))[column addSubview:child];}
        }else{for(NSDictionary *descriptor in BNDescriptors(self,element[@"children"],inner)){NSDictionary *node=descriptor[@"element"];if(![node[@"kind"] isEqual:@"Destination"])[column addSubview:[self renderElement:node locals:descriptor[@"locals"]]];}}
        view=column;
#else
        view=BNRenderNativeNavigation(self,element,locals);
#endif
    }
    else if([kind isEqual:@"Tabs"]){view=BNRenderNativeTabs(self,element,locals);}
    else if([kind isEqual:@"Adaptive"]){BNWindow *window=locals[@"__window"];CGFloat width=window.root.bounds.size.width;if(width<=0)width=MAX(800,[window.definition[@"width"] doubleValue]);NSDictionary *breakpoints=BNDict(self.model[@"layouts"]);CGFloat compact=breakpoints.count ? [breakpoints[@"compact_below"] doubleValue] : 600;NSString *size=width<compact ? @"compact" : !BNIsNull(breakpoints[@"medium_below"]) && width<[breakpoints[@"medium_below"] doubleValue] ? @"medium" : !BNIsNull(breakpoints[@"expanded_below"]) && width>=[breakpoints[@"expanded_below"] doubleValue] ? @"large" : @"expanded";NSDictionary *chosen=nil,*chosenScope=locals;NSArray *order=@[@"compact",@"medium",@"expanded",@"large"];NSUInteger wanted=[order indexOfObject:size],distance=NSUIntegerMax;for(NSDictionary *descriptor in BNDescriptors(self,element[@"children"],locals)){NSDictionary *node=descriptor[@"element"],*scope=descriptor[@"locals"];NSString *candidate=BNPropString(self,node,@"size",scope);NSUInteger at=[order indexOfObject:candidate];if(at==NSNotFound)continue;NSUInteger d=at>=wanted ? at-wanted : 10+wanted-at;if(d<distance){distance=d;chosen=node;chosenScope=scope;}}BNLayout *column=BNContainer(@"column",0);column.fillWidth=YES;column.fillHeight=YES;for(BNView *child in BNRendered(self,chosen[@"children"],chosenScope))[column addSubview:child];view=column;}
    else if([kind isEqual:@"Modal"]){view=BNRenderModal(self,element,locals);}
    else if([kind isEqual:@"Pinch"] || [kind isEqual:@"Swipe"]){view=BNRenderGesture(self,element,locals);}
    else if([kind isEqual:@"Marquee"]){view=BNRenderMarquee(self,element,locals);}
    else if([kind isEqual:@"Drop"]){view=BNRenderDrop(self,element,locals);}
    else if([kind isEqual:@"Svg"]){view=BNRenderSvg(self,element,locals);}
    else if([kind isEqual:@"Query"]){view=[self renderQuery:element locals:locals];}
    else if([kind isEqual:@"Inspector"]){
        if(!BNPropBool(self,element,@"presented",locals,NO))return [[BNView alloc] initWithFrame:CGRectZero];BNWindow *window=locals[@"__window"];
        if(window.root.bounds.size.width>0 && window.root.bounds.size.width<600){NSMutableDictionary *modal=[element mutableCopy],*modalProps=[props mutableCopy];modal[@"kind"]=@"Modal";modalProps[@"cover"]=@{@"kind":@"keyword",@"value":@"compact"};modal[@"props"]=modalProps;NSMutableArray *children=[BNArray(element[@"children"]) mutableCopy];NSDictionary *field=BNDict(props[@"presented"])[@"field"];if(field){NSDictionary *close=@{@"node":@"element",@"kind":@"Button",@"id":@"bern_inspector_close",@"path":[BNString(element[@"path"]) stringByAppendingString:@".close"],@"props":@{@"label":BNTextProperty([self frameworkText:@"bern.window.done" fallback:@"Done"])},@"children":@[],@"action":@{@"kind":@"session",@"field":field,@"op":@{@"kind":@"set",@"value":@{@"kind":@{@"kind":@"literal",@"value":@{@"bool":@NO}},@"type":@{@"kind":@"bool"}}}}};[children addObject:close];}modal[@"children"]=children;view=BNRenderModal(self,modal,locals);}
        else{BNLayout *column=BNContainer(@"column",8);column.requestedWidth=BNPropNumber(self,element,@"width",locals,260);column.fillHeight=YES;column.padding=12;for(BNView *child in BNRendered(self,element[@"children"],locals))[column addSubview:child];BNLayer(column).backgroundColor=BNRole(@"surface.panel").CGColor;view=column;}
    }
    else if([kind isEqual:@"Toast"]){
        NSString *content=BNPropString(self,element,@"content",locals);BNWindow *window=locals[@"__window"];static const void *toastKey=&toastKey;NSMutableDictionary *toasts=objc_getAssociatedObject(window,toastKey);if(!toasts){toasts=[NSMutableDictionary dictionary];objc_setAssociatedObject(window,toastKey,toasts,OBJC_ASSOCIATION_RETAIN_NONATOMIC);}NSString *identity=[NSString stringWithFormat:@"%@/%@%@",locals[@"__component"] ?: @"",element[@"path"],locals[@"__keys"] ?: @""];id key=[self prop:element name:@"key" locals:locals];if(BNIsNull(key))key=content;NSDictionary *old=toasts[identity];BOOL fresh=![old[@"key"] isEqual:key];NSTimeInterval now=NSDate.timeIntervalSinceReferenceDate,duration=MAX(0,BNPropNumber(self,element,@"duration",locals,2.5));if(fresh){toasts[identity]=@{@"key":key ?: BNNull(),@"until":@(now+duration)};__weak BNHost *host=self;dispatch_after(dispatch_time(DISPATCH_TIME_NOW,(int64_t)(duration*NSEC_PER_SEC)),dispatch_get_main_queue(),^{[host scheduleRender];});}if(!content.length || now>=[toasts[identity][@"until"] doubleValue])view=[[BNView alloc] initWithFrame:CGRectZero];else{BNLayout *toast=BNContainer(@"row",6);toast.paddingX=12;toast.paddingY=8;[toast addSubview:BNLabel(self,content,element,locals)];BNLayer(toast).backgroundColor=BNRole(@"surface.raised").CGColor;BNLayer(toast).cornerRadius=16;view=toast;}
    }
    else {
        NSString *axis=[kind isEqual:@"Row"] || [kind isEqual:@"ControlGroup"] || [kind isEqual:@"Toolbar"] ? @"row" : [kind isEqual:@"Stack"] || [kind isEqual:@"Positioned"] || [kind isEqual:@"Modal"] ? @"stack" : [kind isEqual:@"Grid"] ? @"grid" : [kind isEqual:@"Flow"] ? @"flow" : [kind isEqual:@"Rail"] ? @"rail" : [kind isEqual:@"Accordion"] ? @"accordion" : [kind isEqual:@"ScaleBox"] ? @"scale" : @"column";
        BNLayout *container=BNContainer(axis,gap);container.overlay=[axis isEqual:@"stack"];container.alignment=BNPropString(self,element,@"align",locals);if(!container.alignment.length)container.alignment=[axis isEqual:@"stack"] ? @"center" : [axis isEqual:@"row"] ? @"center" : @"leading";
        if([kind isEqual:@"Section"]){NSString *title=BNPropString(self,element,@"title",locals);if(title.length){BNView *annotation=BNLabel(self,title,@{@"props":@{@"style":@{@"kind":@"keyword",@"value":@"headline"}}},locals);NSMutableDictionary *meta=[BNMeta(annotation) mutableCopy];meta[@"sectionAnnotation"]=@YES;BNSetMeta(annotation,meta);[container addSubview:annotation];}}
        NSMutableArray *inspectors=[NSMutableArray array];for(NSDictionary *descriptor in BNDescriptors(self,element[@"children"],locals)){NSDictionary *childElement=descriptor[@"element"];BNView *child=[self renderElement:childElement locals:descriptor[@"locals"]];if([childElement[@"kind"] isEqual:@"Inspector"] && BNPropBool(self,childElement,@"presented",descriptor[@"locals"],NO) && [child isKindOfClass:BNLayout.class])[inspectors addObject:child];else if(child)[container addSubview:child];}
        if([kind isEqual:@"Section"]){NSString *footer=BNPropString(self,element,@"footer",locals);if(footer.length){BNView *annotation=BNLabel(self,footer,@{@"props":@{@"style":@{@"kind":@"keyword",@"value":@"footnote"},@"emphasis":@{@"kind":@"keyword",@"value":@"secondary"}}},locals);NSMutableDictionary *meta=[BNMeta(annotation) mutableCopy];meta[@"sectionAnnotation"]=@YES;BNSetMeta(annotation,meta);[container addSubview:annotation];}}
        BOOL fill=[@[@"Detail",@"Section",@"Toolbar",@"Grid",@"Form",@"Modal",@"Stack"] containsObject:kind];container.fillWidth=fill;container.fillHeight=[@[@"Detail",@"Stack",@"Modal"] containsObject:kind];
        NSMutableDictionary *metadata=[NSMutableDictionary dictionary];
        if([axis isEqual:@"grid"]){metadata[@"minimum"]=@(BNPropNumber(self,element,@"min_width",locals,100));metadata[@"rowGap"]=@(BNPropNumber(self,element,@"row_gap",locals,gap));metadata[@"ratio"]=@(BNPropNumber(self,element,@"cell_ratio",locals,0));metadata[@"extra"]=@(BNPropNumber(self,element,@"cell_extra",locals,0));}
        if([axis isEqual:@"rail"]){metadata[@"vertical"]=@([BNPropString(self,element,@"axis",locals) isEqual:@"vertical"]);metadata[@"overhang"]=@(BNPropNumber(self,element,@"overhang",locals,0));NSString *anchor=BNPropString(self,element,@"anchor",locals);metadata[@"anchor"]=@([anchor isEqual:@"start"] ? 0 : [anchor isEqual:@"end"] ? 1 : 0.5);}
        if([axis isEqual:@"accordion"]){metadata[@"height"]=@(BNPropNumber(self,element,@"height",locals,0));metadata[@"collapsed"]=@(BNPropNumber(self,element,@"collapsed_width",locals,0));metadata[@"selected"]=@(BNPropNumber(self,element,@"selected",locals,0));metadata[@"corner"]=@(BNPropNumber(self,element,@"corner",locals,0));}
        if([axis isEqual:@"scale"]){metadata[@"designWidth"]=@(BNPropNumber(self,element,@"width",locals,1));metadata[@"designHeight"]=@(BNPropNumber(self,element,@"height",locals,1));}
        if([axis isEqual:@"scale"]){BNLayout *scene=BNContainer(@"stack",0);scene.overlay=YES;scene.alignment=@"top_leading";for(BNView *child in [container.subviews copy]){[child removeFromSuperview];[scene addSubview:child];}[container addSubview:scene];container.fillWidth=YES;container.fillHeight=YES;BNLayer(container).masksToBounds=YES;}
        BNSetMeta(container,metadata);view=container;if(inspectors.count){BNLayout *split=BNContainer(@"row",1);split.fillWidth=YES;split.fillHeight=YES;container.fillWidth=YES;container.fillHeight=YES;[split addSubview:container];for(BNView *inspector in inspectors)[split addSubview:inspector];view=split;}
    }
    if(!view)view=[[BNView alloc] initWithFrame:CGRectZero];
    if([BNPropString(self,element,@"reveal",locals) isEqual:@"hover"] && ![view isKindOfClass:BNLayout.class]){BNLayout *wrapper=BNContainer(@"stack",0);wrapper.alignment=@"center";[wrapper addSubview:view];view=wrapper;}
    NSMutableDictionary *metadata=[BNMeta(view) mutableCopy];metadata[@"kind"]=kind;metadata[@"element"]=element;metadata[@"locals"]=locals;if(locals[@"__itemKey"])metadata[@"itemKey"]=locals[@"__itemKey"];
    for(NSString *name in @[@"width",@"height",@"at",@"from",@"to",@"x",@"y"]){if(([@[@"ScaleBox",@"Search"] containsObject:kind]) && [@[@"width",@"height"] containsObject:name])continue;id value=[self prop:element name:name locals:locals];if(!BNIsNull(value)){if([value isKindOfClass:NSString.class] && [value isEqual:@"fill"]){metadata[[name isEqual:@"height"] ? @"fillHeight" : @"fillWidth"]=@YES;metadata[@"grow"]=@YES;metadata[@"growAxis"]=[name isEqual:@"height"] ? @"vertical" : @"horizontal";}else if([value respondsToSelector:@selector(doubleValue)])metadata[name]=@([value doubleValue]);}}
    if([view isKindOfClass:BNLayout.class]){BNLayout *layout=(BNLayout *)view;layout.padding=BNPropNumber(self,element,@"padding",locals,0);layout.paddingX=BNPropNumber(self,element,@"padding_x",locals,layout.padding)-layout.padding;layout.paddingY=BNPropNumber(self,element,@"padding_y",locals,layout.padding)-layout.padding;layout.requestedWidth=[metadata[@"width"] doubleValue];layout.requestedHeight=[metadata[@"height"] doubleValue];if([metadata[@"fillWidth"] boolValue])layout.fillWidth=YES;if([metadata[@"fillHeight"] boolValue])layout.fillHeight=YES;}
    BNSetMeta(view,metadata);BNAccessibility(view,BNString(element[@"id"]),label);
    NSString *appearance=BNPropString(self,element,@"appearance",locals);
#if TARGET_OS_OSX
    if(appearance.length)view.appearance=[appearance isEqual:@"dark"] ? [NSAppearance appearanceNamed:NSAppearanceNameDarkAqua] : [appearance isEqual:@"light"] ? [NSAppearance appearanceNamed:NSAppearanceNameAqua] : nil;
#else
    if(appearance.length)view.overrideUserInterfaceStyle=[appearance isEqual:@"dark"] ? UIUserInterfaceStyleDark : [appearance isEqual:@"light"] ? UIUserInterfaceStyleLight : UIUserInterfaceStyleUnspecified;
#endif
    NSString *shape=BNPropString(self,element,@"shape",locals),*prominence=BNPropString(self,element,@"prominence",locals),*role=BNPropString(self,element,@"role",locals);
    if([view isKindOfClass:BNStyledButton.class] && ([@[@"capsule",@"chip"] containsObject:shape] || [prominence isEqual:@"prominent"])){CGFloat height=[metadata[@"height"] doubleValue];if(height<=0)height=32;BNLayer(view).cornerRadius=height/2;BNColor *accent=[role isEqual:@"destructive"] ? BNRole(@"status.error") : BNRole(@"accent");BNLayer(view).backgroundColor=([prominence isEqual:@"prominent"] ? accent : BNRole(@"fill.subtle")).CGColor;BNTintOnly(view,[prominence isEqual:@"prominent"] ? BNRole(@"on_accent") : BNRole(@"text.primary"));NSMutableDictionary *m=[BNMeta(view) mutableCopy];CGFloat textWidth=0;
#if TARGET_OS_OSX
        NSButton *button=(NSButton *)view;textWidth=button.attributedTitle.size.width+(button.image ? button.image.size.width+(button.title.length ? 5 : 0) : 0);
#else
        UIButton *button=(UIButton *)view;textWidth=[button.titleLabel sizeThatFits:CGSizeMake(100000,height)].width+(button.currentImage ? button.currentImage.size.width+(button.currentTitle.length ? 5 : 0) : 0);
#endif
        m[@"minimumSize"]=@[@(MAX(height,textWidth+28)),@(height)];BNSetMeta(view,m);
#if TARGET_OS_OSX
        [(NSButton *)view setBordered:NO];
#endif
    }
    BOOL enabled=![locals[@"__disabled"] boolValue] && BNPropBool(self,element,@"enabled",locals,YES);NSMutableDictionary *enabledMeta=[BNMeta(view) mutableCopy];enabledMeta[@"disabled"]=@(!enabled);BNSetMeta(view,enabledMeta);
#if TARGET_OS_OSX
    if([view respondsToSelector:@selector(setEnabled:)])[(id)view setEnabled:enabled];
    if([kind isEqual:@"Stack"] && !enabled)[view setAccessibilityChildren:@[]];
#else
    if([view isKindOfClass:UIControl.class])[(UIControl *)view setEnabled:enabled];view.userInteractionEnabled=enabled;
    if([kind isEqual:@"Stack"])view.accessibilityElementsHidden=!enabled;
#endif
    BNApplyStyle(self,view,element,locals,selected);
    if([kind isEqual:@"SearchItem"])BNSearchRegisterResult(self,element,locals,view);
    return view;
}
@end
