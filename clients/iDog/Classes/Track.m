//
//  Track.m
//  iDog
//
//  Created by Johan Nyström on 2009-05-29.
//  Copyright 2009 NoName. All rights reserved.
//

#import "Track.h"

@implementation Song

@synthesize title, artist, album, releaseDate, category;

- (void)dealloc {
    [title release];
    [artist release];
    [album release];
    [releaseDate release];
    [category release];
    [super dealloc];
}

@end
