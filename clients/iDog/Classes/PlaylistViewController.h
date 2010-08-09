//
//  PlaylistViewController.h
//  iDog
//
//  Created by Johan Nyström on 2009-05-26.
//  Copyright 2009 NoName. All rights reserved.
//

#import <UIKit/UIKit.h>


@interface PlaylistViewController : UIViewController <UITableViewDelegate, UITableViewDataSource> {
	UITableView *playlistTableView;
	NSMutableArray *trackItems;
	NSMutableArray *trackURIs;
}

@property (nonatomic, retain) IBOutlet UITableView *playlistTableView;
@property (nonatomic, retain) NSMutableArray *trackItems;
@property (nonatomic, retain) NSMutableArray *trackURIs;

@end
