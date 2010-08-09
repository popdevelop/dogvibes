//
//  TrackViewController.m
//  iDog
//
//  Created by Johan Nyström on 2009-05-27.
//  Copyright 2009 NoName. All rights reserved.
//

#import "TrackViewController.h"
#import "JSON.h"

@implementation TrackViewController

@synthesize jsonLabel, jsonImage, jsonItem, itemID;

- (id)initWithNibName:(NSString *)nibNameOrNil bundle:(NSBundle *)nibBundleOrNil {
	if (self = [super initWithNibName:nibNameOrNil bundle:nibBundleOrNil]) {
		// Initialization code
		self.itemID = 0;
	}
	return self;
}

-(void)setID:(NSInteger)val {
	self.itemID = (NSInteger *)val;
}

- (void)viewDidLoad {
	// init the url	
}

- (BOOL)shouldAutorotateToInterfaceOrientation:(UIInterfaceOrientation)interfaceOrientation {
	// Return YES for supported orientations
	return (interfaceOrientation == UIInterfaceOrientationPortrait);
}

- (void)didReceiveMemoryWarning {
	[super didReceiveMemoryWarning]; // Releases the view if it doesn't have a superview
	// Release anything that's not essential, such as cached data
}

- (void)dealloc {
	[jsonLabel dealloc];
	[jsonImage dealloc];
	[self.jsonItem dealloc];
	[super dealloc];
}

@end
