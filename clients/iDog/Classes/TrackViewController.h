//
//  TrackViewController.h
//  iDog
//
//  Created by Johan Nyström on 2009-05-27.
//  Copyright 2009 NoName. All rights reserved.
//

#import <UIKit/UIKit.h>


@interface TrackViewController : UIViewController {
	IBOutlet UILabel *jsonLabel;
	IBOutlet UIImageView *jsonImage;
	NSDictionary *jsonItem;
	NSInteger *itemID;
}

@property (nonatomic, retain) UILabel *jsonLabel;
@property (nonatomic, retain) UIImageView *jsonImage;
@property (nonatomic, retain) NSDictionary *jsonItem;
@property (nonatomic, assign) NSInteger *itemID;

-(void)setID:(NSInteger)val;

@end
