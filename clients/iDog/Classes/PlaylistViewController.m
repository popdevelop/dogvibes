//
//  PlaylistViewController.m
//  iDog
//
//  Created by Johan Nyström on 2009-05-26.
//  Copyright 2009 NoName. All rights reserved.
//

#import "PlaylistViewController.h"
#import "SettingsViewController.h"
#import "DogUtils.h"
#import "JSON.h"
#import "iDogAppDelegate.h"

@implementation PlaylistViewController

@synthesize playlistTableView, trackItems, trackURIs;

// Implement viewDidLoad to do additional setup after loading the view, typically from a nib.
- (void)viewDidLoad {
	[super viewDidLoad];
	trackItems = [[NSMutableArray alloc] initWithCapacity: 100];
	trackURIs = [[NSMutableArray alloc] initWithCapacity: 100];

	DogUtils *dog = [[DogUtils alloc] init];
	NSString *jsonData = [NSString alloc];
	jsonData = [dog dogRequest:[NSString stringWithFormat:@"/dogvibes/getAllPlaylists", nil]];
	[dog release];
	
	if (jsonData != nil) {
		NSDictionary *trackDict = [jsonData JSONValue];
		NSDictionary *result = [trackDict objectForKey:@"result"];

		for (id key in result) {
			if ([key objectForKey:@"name"]) {
			[trackItems addObject:(NSString *)[key objectForKey:@"name"]];
			}
		}
	}
	[jsonData release];
}

- (NSInteger)tableView:(UITableView *)tableView numberOfRowsInSection:(NSInteger)section {
    return [trackItems count];
}

- (UITableViewCell *)tableView:(UITableView *)tv cellForRowAtIndexPath:(NSIndexPath *)indexPath {
    static NSString *kCellIdentifier = @"MyCell";
    UITableViewCell *cell = [playlistTableView dequeueReusableCellWithIdentifier:kCellIdentifier];
    if (cell == nil) {
        cell = [[[UITableViewCell alloc] initWithFrame:CGRectZero reuseIdentifier:kCellIdentifier] autorelease];
        cell.accessoryType = UITableViewCellAccessoryDisclosureIndicator;
    }
    cell.text = [trackItems objectAtIndex:indexPath.row];
    return cell;
}

- (void)tableView:(UITableView *)table didSelectRowAtIndexPath:(NSIndexPath *)indexPath {
	// do something with the view or play the song...
}

- (void)viewWillAppear:(BOOL)animated {
	[super viewWillAppear:animated];
}

- (void)viewDidAppear:(BOOL)animated {
	[super viewDidAppear:animated];
}

- (void)viewWillDisappear:(BOOL)animated {
}

- (void)viewDidDisappear:(BOOL)animated {
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
	NSLog(@"memory freed!");
	
    [super dealloc];
	[trackItems dealloc];
	[trackURIs dealloc];
	[playlistTableView dealloc];
}

@end
