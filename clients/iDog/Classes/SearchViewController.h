//
//  SearchViewController.h
//  iDog
//
//  Created by Johan Nyström on 2009-05-26.
//  Copyright 2009 NoName. All rights reserved.
//

#import <UIKit/UIKit.h>

@interface SearchViewController : UIViewController <UITableViewDelegate, UITableViewDataSource, UISearchBarDelegate> {
	NSMutableArray *jsonArray;
	NSDictionary *jsonItem;
	UISearchBar *mySearchBar;
	UITableView *myTableView;
	
	NSArray						*listContent;			// the master content
	NSMutableArray				*filteredListContent;	// the filtered content as a result of the search
	NSMutableArray				*savedContent;			// the saved content in case the user cancels a search
	
	NSMutableArray *trackItems;
	NSMutableArray *trackURIs;

	NSString *mySearchText;
}

@property (nonatomic, retain) NSMutableArray *jsonArray;
@property (nonatomic, retain) NSDictionary *jsonItem;
@property (nonatomic, retain) IBOutlet UISearchBar *mySearchBar;
@property (nonatomic, retain) IBOutlet UITableView *myTableView;

@property (nonatomic, retain) NSArray *listContent;
@property (nonatomic, retain) NSMutableArray *filteredListContent;
@property (nonatomic, retain) NSMutableArray *savedContent;
@property (nonatomic, retain) NSMutableArray *trackItems;
@property (nonatomic, retain) NSMutableArray *trackURIs;
@property (nonatomic, retain) NSString *mySearchText;

@end
