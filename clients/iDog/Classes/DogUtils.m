//
//  DogUtils.m
//  iDog
//
//  Created by Johan Nyström on 2009-11-16.
//  Copyright 2009 __MyCompanyName__. All rights reserved.
//

#import "DogUtils.h"
#import "JSON.h"
#import "iDogAppDelegate.h"
#import "SettingsViewController.h"

@implementation DogUtils

/* TODO!: asynchronous http requests */
- (NSString *)dogRequest:(NSString *)request {
	iDogAppDelegate *iDogApp = (iDogAppDelegate *)[[UIApplication sharedApplication] delegate];
	NSString *ip = iDogApp.dogIP;
	
	int stringLength = [request length];
	NSRange range = NSMakeRange(0, stringLength);
	NSString *newStr = [request stringByReplacingOccurrencesOfString:@" " withString:@"%20" options:NSCaseInsensitiveSearch range:range];	
	
	if (ip != nil) {
		NSLog(@"dog: %@, %@", ip, request);
		//synchronous...
		NSURL *jsonURL = [NSURL URLWithString:[NSString stringWithFormat:@"http://%@%@",ip, newStr, nil]];
		NSString *jsonData = [[NSString alloc] initWithContentsOfURL:jsonURL];
		//asynchronous: TODO..
		if (jsonData == nil) {NSLog(@"NULL!"); return nil;}
		return jsonData;
	} else {
		return nil;
	}
}

- (UIImage *) dogGetAlbumArt:(NSString *)uri {
	iDogAppDelegate *iDogApp = (iDogAppDelegate *)[[UIApplication sharedApplication] delegate];
	NSString *ip = iDogApp.dogIP;
	if (ip != nil) {
		return [UIImage imageWithData: 
				[NSData dataWithContentsOfURL: 
				 [NSURL URLWithString:
				  [NSString stringWithFormat:
				   @"http://%@/dogvibes/getAlbumArt?size=159&uri=%@",ip, uri, nil]]]];
	} else {
		return nil;
	}
}

@end