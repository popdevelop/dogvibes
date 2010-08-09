//
//  SearchViewController.m
//  iDog
//
//  Created by Johan Nyström on 2009-05-26.
//  Copyright 2009 NoName. All rights reserved.
//

#import "SearchViewController.h"
#import "SettingsViewController.h"
#import "TrackViewController.h"
#import "iDogAppDelegate.h"
#import "DogUtils.h"

#import "JSON/JSON.h"

@implementation SearchViewController

@synthesize jsonArray, jsonItem, mySearchBar, myTableView, mySearchText;
@synthesize listContent, filteredListContent, savedContent, trackItems, trackURIs;

- (void)viewDidLoad {
    [super viewDidLoad];
}

- (void)awakeFromNib
{	
	// create the master list
	listContent = [[NSArray alloc] initWithObjects:	@"Please search for a song!", nil];
	
	// create our filtered list that will be the data source of our table, start its content from the master "listContent"
	
	//filteredListContent = [[NSMutableArray alloc] initWithCapacity: [listContent count]];
	trackItems = [[NSMutableArray alloc] initWithCapacity: 1000];
	trackURIs = [[NSMutableArray alloc] initWithCapacity: 1000];
	[trackItems addObjectsFromArray: listContent];
	
	// this stored the current list in case the user cancels the filtering
	//savedContent = [[NSMutableArray alloc] initWithCapacity: [listContent count]]; 
	
	// don't get in the way of user typing
	mySearchBar.autocorrectionType = UITextAutocorrectionTypeNo;
	mySearchBar.autocapitalizationType = UITextAutocapitalizationTypeNone;
	mySearchBar.showsCancelButton = NO;
}

#pragma mark UIViewController

- (void)viewWillAppear:(BOOL)animated
{
	NSIndexPath *tableSelection = [myTableView indexPathForSelectedRow];
	[myTableView deselectRowAtIndexPath:tableSelection animated:NO];
}

- (void)didReceiveMemoryWarning {
    [super didReceiveMemoryWarning]; // Releases the view if it doesn't have a superview
    // Release anything that's not essential, such as cached data
}

#pragma mark Table view methods

- (NSInteger)numberOfSectionsInTableView:(UITableView *)tableView {
    return 1;
}

// Customize the number of rows in the table view.
- (NSInteger)tableView:(UITableView *)tableView numberOfRowsInSection:(NSInteger)section {
    return [trackItems count];
}


- (UITableViewCell *)tableView:(UITableView *)tv cellForRowAtIndexPath:(NSIndexPath *)indexPath {
    static NSString *kCellIdentifier = @"MyCell";
    UITableViewCell *cell = [myTableView dequeueReusableCellWithIdentifier:kCellIdentifier];
    if (cell == nil) {
        cell = [[[UITableViewCell alloc] initWithFrame:CGRectZero reuseIdentifier:kCellIdentifier] autorelease];
        cell.accessoryType = UITableViewCellAccessoryDisclosureIndicator;
    }
    cell.text = [trackItems objectAtIndex:indexPath.row];
    return cell;
}

- (void)tableView:(UITableView *)tableView didSelectRowAtIndexPath:(NSIndexPath *)indexPath {
	NSLog(@"adding %@ to playqueue", [trackURIs objectAtIndex:indexPath.row]);
	NSLog(@"Play this song title: %@, %@!", [trackItems objectAtIndex:indexPath.row], [trackURIs objectAtIndex:indexPath.row]);
	DogUtils *dog = [[DogUtils alloc] init];
	NSString *jsonData = [NSString alloc];
	jsonData = [dog dogRequest:[NSString stringWithFormat:@"/amp/0/queue?uri=%@",[trackURIs objectAtIndex:indexPath.row], nil]];
	
	if (jsonData == nil) {
		UIAlertView *alert = [[UIAlertView alloc] initWithTitle:@"No reply from server!" message:@"Either the webservice is down (verify with Statusbutton under setting) or else, there's nothing added in playlist."  delegate:self cancelButtonTitle:@"OK" otherButtonTitles: nil];
		[alert show];
		[alert release];
	}
	[dog release];
	[jsonData release];
}

#pragma mark UISearchBarDelegate

- (void)searchBarTextDidBeginEditing:(UISearchBar *)searchBar
{
	// only show the status bar's cancel button while in edit mode
	mySearchBar.showsCancelButton = YES;
	
	// flush and save the current list content in case the user cancels the search later
	[savedContent removeAllObjects];
	[savedContent addObjectsFromArray: trackItems];
}

- (void)searchBarTextDidEndEditing:(UISearchBar *)searchBar
{
	mySearchBar.showsCancelButton = NO;
}

- (void)searchBar:(UISearchBar *)searchBar textDidChange:(NSString *)searchText
{
	[trackItems removeAllObjects];	// clear the filtered array first
	[trackURIs removeAllObjects];
	mySearchText = [searchText retain];
}

// called when cancel button pressed
- (void)searchBarCancelButtonClicked:(UISearchBar *)searchBar
{
	NSLog(@"Cancelled search!");
	// if a valid search was entered but the user wanted to cancel, bring back the saved list content
	if (searchBar.text.length > 0)
	{
		[trackItems removeAllObjects];
	}
	[myTableView reloadData];
	[searchBar resignFirstResponder];
	searchBar.text = @"";
}

// called when Search (in our case "Done") button pressed
- (void)searchBarSearchButtonClicked:(UISearchBar *)searchBar
{
	NSLog(@"searchButtonClicked!");
	
	DogUtils *dog = [[DogUtils alloc] init];
	NSString *jsonData = [NSString alloc];
	jsonData = [dog dogRequest:[NSString stringWithFormat:@"/dogvibes/search?query=%@",mySearchText, nil]];
	[dog release];
	if (jsonData != nil) {
		jsonArray = [jsonData JSONValue];
		NSDictionary *tsdic = [jsonData JSONValue];
		for (id key in [tsdic objectForKey:@"result"]) {
			[trackItems addObject:(NSString *)[key objectForKey:@"title"]];
			[trackURIs addObject:(NSString *)[key objectForKey:@"uri"]];
		}
		[myTableView reloadData];
	}
	[jsonData release];
	[searchBar resignFirstResponder];
}

- (void)dealloc {
	[myTableView release];
	[mySearchBar release];
	[listContent release];
	[filteredListContent release];
	[savedContent release];
	[trackItems release];
	[trackURIs release];
	[super dealloc];
}

@end