//
//  Track.h
//  iDog
//
//  Created by Johan Nyström on 2009-05-29.
//  Copyright 2009 NoName. All rights reserved.
//

#import <UIKit/UIKit.h>

@interface Song : NSObject {
@private
    NSString *title;
    NSString *artist;
    NSString *album;
    NSDate *releaseDate;
    NSString *category;
}

@property (nonatomic, copy) NSString *title;
@property (nonatomic, copy) NSString *artist;
@property (nonatomic, copy) NSString *album;
@property (nonatomic, copy) NSDate *releaseDate;
@property (nonatomic, copy) NSString *category;

@end
