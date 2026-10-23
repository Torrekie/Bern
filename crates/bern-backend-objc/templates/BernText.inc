// Bern message formatting. Mirrors bern-protocol/format.rs on Darwin 20.
// Month and weekday names come from the same generated framework text table.
typedef NSString * (^BNTextName)(NSString *);
#include <stdio.h>
#include <stdlib.h>
#include <xlocale.h>

// The shortest decimal that round-trips to the value, expanded without an
// exponent as Rust's f64 Display does. Exact plural selectors compare this
// spelling, so =01 must not accidentally match the number 1.
static NSString *BNNumberText(double value) {
    if(isnan(value)) return @"NaN";
    if(isinf(value)) return value<0 ? @"-inf" : @"inf";
    static locale_t decimalLocale;
    static dispatch_once_t once;
    dispatch_once(&once, ^{ decimalLocale=newlocale(LC_NUMERIC_MASK,"C",NULL); });
    char buffer[64];
    for(int digits=1;digits<=17;digits++) {
        snprintf_l(buffer,sizeof(buffer),decimalLocale,"%.*g",digits,value);
        if(strtod_l(buffer,NULL,decimalLocale)==value) break;
    }
    NSString *text=[NSString stringWithUTF8String:buffer];
    NSRange exponent=[text rangeOfString:@"e"];
    if(exponent.location==NSNotFound) return text;
    NSInteger power=[[text substringFromIndex:exponent.location+1] integerValue];
    NSString *mantissa=[text substringToIndex:exponent.location];
    NSString *sign=[mantissa hasPrefix:@"-"] ? @"-" : @"";
    if(sign.length) mantissa=[mantissa substringFromIndex:1];
    NSRange point=[mantissa rangeOfString:@"."];
    NSInteger decimal=(point.location==NSNotFound ? (NSInteger)mantissa.length : (NSInteger)point.location)+power;
    NSString *digits=[mantissa stringByReplacingOccurrencesOfString:@"." withString:@""];
    if(decimal<=0) return [NSString stringWithFormat:@"%@0.%@%@",sign,[@"" stringByPaddingToLength:(NSUInteger)-decimal withString:@"0" startingAtIndex:0],digits];
    if(decimal>=(NSInteger)digits.length) return [NSString stringWithFormat:@"%@%@%@",sign,digits,[@"" stringByPaddingToLength:(NSUInteger)(decimal-(NSInteger)digits.length) withString:@"0" startingAtIndex:0]];
    return [NSString stringWithFormat:@"%@%@.%@",sign,[digits substringToIndex:(NSUInteger)decimal],[digits substringFromIndex:(NSUInteger)decimal]];
}

static NSString *BNTrim(NSString *text) {
    return [text stringByTrimmingCharactersInSet:[NSCharacterSet whitespaceAndNewlineCharacterSet]];
}

static NSString *BNArgumentText(id value) {
    if (BNIsNull(value)) return @"";
    if ([value isKindOfClass:[NSDictionary class]]) {
        if (value[@"text"]) return BNString(value[@"text"]);
        if (value[@"year"] && value[@"month"] && value[@"day"])
            return [NSString stringWithFormat:@"%04lld-%02lld-%02lld", [value[@"year"] longLongValue], [value[@"month"] longLongValue], [value[@"day"] longLongValue]];
    }
    return BNString(value);
}

static double BNArgumentNumber(id value) {
    if ([value isKindOfClass:[NSDictionary class]]) value=value[@"number"] ?: value[@"text"];
    return [value respondsToSelector:@selector(doubleValue)] ? [value doubleValue] : 0;
}

static NSString *BNDuration(NSString *pattern, double value) {
    // Rust's saturating f64 -> i64 conversion caps very large durations.
    int64_t total = !isfinite(value) || value <= 0 ? 0 : value >= (double)INT64_MAX ? INT64_MAX : (int64_t)floor(value);
    BOOL hours=[pattern rangeOfString:@"h"].location!=NSNotFound;
    BOOL minutes=[pattern rangeOfString:@"m"].location!=NSNotFound;
    NSMutableString *out=[NSMutableString string];
    for(NSUInteger i=0;i<pattern.length;) {
        unichar c=[pattern characterAtIndex:i]; NSUInteger end=i+1;
        while(end<pattern.length && [pattern characterAtIndex:end]==c) end++;
        int64_t n=0; BOOL field=YES;
        switch(c) {
            case 'h': n=total/3600; break;
            case 'm': n=hours ? total%3600/60 : total/60; break;
            case 's': n=minutes||hours ? total%60 : total; break;
            default: field=NO; break;
        }
        if(field) [out appendFormat:end-i==2 ? @"%02lld" : @"%lld",(long long)n];
        else [out appendString:[pattern substringWithRange:NSMakeRange(i,end-i)]];
        i=end;
    }
    return out;
}

static int64_t BNFloorDiv(int64_t value, int64_t divisor) {
    int64_t q=value/divisor, r=value%divisor;
    return q-(r<0);
}

static NSString *BNDate(NSString *pattern, id date, BNTextName name) {
    int64_t year=0,month=0,day=0;
    if([date isKindOfClass:[NSDictionary class]]) {
        year=[date[@"year"] longLongValue]; month=[date[@"month"] longLongValue]; day=[date[@"day"] longLongValue];
    } else if([date isKindOfClass:[NSArray class]] && [date count]>=3) {
        year=[date[0] longLongValue]; month=[date[1] longLongValue]; day=[date[2] longLongValue];
    } else return @"";
    static const int offsets[]={0,3,2,5,0,3,5,1,4,6,2,4};
    int64_t m=MAX(1,MIN(12,month)), y=month<3 ? year-1 : year;
    int64_t weekday=(y+BNFloorDiv(y,4)-BNFloorDiv(y,100)+BNFloorDiv(y,400)+offsets[m-1]+day)%7;
    if(weekday<0) weekday+=7;
    weekday=(weekday+6)%7+1; // Bern numbers weekdays from Monday = 1.
    NSMutableString *out=[NSMutableString string];
    for(NSUInteger i=0;i<pattern.length;) {
        unichar c=[pattern characterAtIndex:i]; NSUInteger end=i+1;
        while(end<pattern.length && [pattern characterAtIndex:end]==c) end++;
        NSUInteger n=end-i;
        if(c=='y') {
            if(n==2) [out appendFormat:@"%02lld", (long long)((year%100+100)%100)];
            else [out appendFormat:@"%lld",(long long)year];
        } else if(c=='M' && n>=3) {
            NSString *key=[NSString stringWithFormat:n==3?@"bern.date.month.%lld":@"bern.date.month_long.%lld",(long long)month];
            [out appendString:name ? name(key) : key];
        } else if(c=='E') {
            NSString *key=[NSString stringWithFormat:n==3?@"bern.date.weekday.%lld":@"bern.date.weekday_long.%lld",(long long)weekday];
            [out appendString:name ? name(key) : key];
        } else if(c=='M'||c=='d') {
            [out appendFormat:n==1?@"%lld":@"%02lld", (long long)(c=='M'?month:day)];
        } else [out appendString:[pattern substringWithRange:NSMakeRange(i,n)]];
        i=end;
    }
    return out;
}

static NSString *BNMessage(NSString *, NSUInteger *, BOOL, NSDictionary *, NSString *, BNTextName, NSString *);

static NSString *BNPlaceholder(NSString *pattern, NSUInteger *position, NSDictionary *args, NSString *language, BNTextName name) {
    NSUInteger start=*position;
    while(*position<pattern.length && [pattern characterAtIndex:*position]!=',' && [pattern characterAtIndex:*position]!='}') (*position)++;
    NSString *key=BNTrim([pattern substringWithRange:NSMakeRange(start,*position-start)]);
    id arg=args[key];
    if(*position>=pattern.length) return @"";
    if([pattern characterAtIndex:*position]=='}') { (*position)++; return BNArgumentText(arg); }
    (*position)++; start=*position;
    while(*position<pattern.length && [pattern characterAtIndex:*position]!=',' && [pattern characterAtIndex:*position]!='}') (*position)++;
    NSString *kind=BNTrim([pattern substringWithRange:NSMakeRange(start,*position-start)]);
    if(*position>=pattern.length) return @"";
    (*position)++;
    if([kind isEqualToString:@"plural"]) {
        double number=BNArgumentNumber(arg);
        NSString *hash=BNArgumentText(arg);
        NSString *base=[[language stringByReplacingOccurrencesOfString:@"_" withString:@"-"] componentsSeparatedByString:@"-"].firstObject;
        BOOL one=![@[@"zh",@"ja",@"ko",@"vi",@"th",@"id",@"ms"] containsObject:base] && number==1;
        NSString *category=one?@"one":@"other";
        NSString *exact=nil,*selected=nil,*other=nil;
        NSCharacterSet *space=[NSCharacterSet whitespaceAndNewlineCharacterSet];
        while(*position<pattern.length) {
            while(*position<pattern.length && [space characterIsMember:[pattern characterAtIndex:*position]]) (*position)++;
            if(*position>=pattern.length) break;
            if([pattern characterAtIndex:*position]=='}') { (*position)++; break; }
            start=*position;
            while(*position<pattern.length && [pattern characterAtIndex:*position]!='{') (*position)++;
            NSString *selector=BNTrim([pattern substringWithRange:NSMakeRange(start,*position-start)]);
            if(*position>=pattern.length) break;
            (*position)++;
            NSString *body=BNMessage(pattern,position,YES,args,language,name,hash);
            if([selector isEqualToString:[@"=" stringByAppendingString:BNNumberText(number)]]) exact=body;
            if([selector isEqualToString:category]) selected=body;
            if([selector isEqualToString:@"other"]) other=body;
        }
        return exact ?: selected ?: other ?: @"";
    }
    start=*position;
    while(*position<pattern.length && [pattern characterAtIndex:*position]!='}') (*position)++;
    NSString *format=BNTrim([pattern substringWithRange:NSMakeRange(start,*position-start)]);
    if(*position<pattern.length) (*position)++;
    if([kind isEqualToString:@"duration"]) return BNDuration(format,BNArgumentNumber(arg));
    if([kind isEqualToString:@"date"]) return BNDate(format,arg,name);
    return @"";
}

static NSString *BNMessage(NSString *pattern, NSUInteger *position, BOOL branch, NSDictionary *args, NSString *language, BNTextName name, NSString *hash) {
    NSMutableString *out=[NSMutableString string];
    while(*position<pattern.length) {
        unichar c=[pattern characterAtIndex:(*position)++];
        if(c=='}' && branch) break;
        if((c=='{'||c=='}') && *position<pattern.length && [pattern characterAtIndex:*position]==c) {
            (*position)++; [out appendFormat:@"%C",c];
        } else if(c=='{') [out appendString:BNPlaceholder(pattern,position,args,language,name)];
        else if(c=='#' && hash) [out appendString:hash];
        else [out appendFormat:@"%C",c];
    }
    return out;
}

static NSString *BNFormat(NSString *pattern, NSDictionary *args, NSString *language, BNTextName name) {
    NSUInteger position=0;
    return BNMessage(pattern ?: @"",&position,NO,args ?: @{},language ?: @"en",name,nil);
}
