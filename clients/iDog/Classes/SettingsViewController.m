//
//  SettingsViewController.m
//  iDog
//
//  Created by Johan Nyström on 2009-05-26.
//  Copyright 2009 NoName. All rights reserved.
//

#import "iDogAppDelegate.h"
#import "SettingsViewController.h"

@implementation SettingsViewController

static SettingsViewController *sharedViewController;

// Implement viewDidLoad to do additional setup after loading the view, typically from a nib.
- (void)viewDidLoad {
	[super viewDidLoad];
	
	iDogAppDelegate *iDogApp = (iDogAppDelegate *)[[UIApplication sharedApplication] delegate];
	NSLog(@"%@", iDogApp.dogIP);
	if (iDogApp.dogIP != nil) {
	  IPtextField.text = iDogApp.dogIP;
	}
    
}

- (IBAction)statusButtonPressed:(id)sender
{
	NSURL *jsonURL = [NSURL URLWithString:[NSString stringWithFormat:@"http://%@/amp/0/getStatus",[self getIPfromTextField], nil]];
	NSString *jsonData = [[NSString alloc] initWithContentsOfURL:jsonURL];
	
	if (jsonData == nil) {
		UIAlertView *alert = [[UIAlertView alloc] initWithTitle:@"Webservice Down" message:@"The webservice you are accessing is down. Please try again later."  delegate:self cancelButtonTitle:@"OK" otherButtonTitles: nil];
		[alert show];
		[alert release];
	} else {
		label.text = jsonData;
	}
}

/* gui handlers */
- (IBAction)slider0Changed:(id)sender
{
	NSString *jsonData;
	NSURL *jsonURL;
	if ( spk0.on )
		jsonURL = [NSURL URLWithString:[NSString stringWithFormat:@"http://%@/amp/0/connectSpeaker?nbr=0",[self getIPfromTextField], nil]];
	else
		jsonURL = [NSURL URLWithString:[NSString stringWithFormat:@"http://%@/amp/0/disconnectSpeaker?nbr=0", [self getIPfromTextField], nil]];
	
	jsonData = [[NSString alloc] initWithContentsOfURL:jsonURL];
	if (jsonData == nil) {
		UIAlertView *alert = [[UIAlertView alloc] initWithTitle:@"Webservice Down" message:@"The webservice you are accessing is down. Please try again later."  delegate:self cancelButtonTitle:@"OK" otherButtonTitles: nil];
		[alert show];
		[alert release];
	}
}

- (IBAction)IPtextFieldChanged:(id)sender
{
	[IPtextField resignFirstResponder];
	iDogAppDelegate *iDogApp = (iDogAppDelegate *)[[UIApplication sharedApplication] delegate];
	textView.text = IPtextField.text;
	iDogApp.dogIP = [(NSString *)CFURLCreateStringByAddingPercentEscapes(
																		 nil,
																		 (CFStringRef)[IPtextField text],
																		 NULL,
																		 NULL,
																		 kCFStringEncodingUTF8) autorelease];
	[[NSUserDefaults standardUserDefaults] setObject:iDogApp.dogIP forKey:iDogApp.kDogVibesIP];
	[[NSUserDefaults standardUserDefaults] synchronize];
}

- (NSString *)getIPfromTextField {
	NSString *escapedIPValue =
	[(NSString *)CFURLCreateStringByAddingPercentEscapes(
														 nil,
														 (CFStringRef)[IPtextField text],
														 NULL,
														 NULL,
														 kCFStringEncodingUTF8) autorelease];
	if ([escapedIPValue length] > 0) {
		return escapedIPValue;
	} else { 
		return nil;
	}
}

-(void)setIPTextField:(NSString *)text
{
	if (text != nil)
		IPtextField.text = text;
}

- (BOOL)textFieldShouldReturn:(UITextField *)theTextField 
{
    if ( theTextField == IPtextField ) {
		[self IPtextFieldChanged:theTextField];
		[IPtextField resignFirstResponder];
	}
    return YES;
}

+(SettingsViewController *)sharedViewController {
	if (!sharedViewController)
		sharedViewController = [[SettingsViewController alloc] init];
	return sharedViewController;
}

+(id)alloc
{
	NSAssert(sharedViewController == nil, @"Attempted to allocate a second instance of a singleton.");
	sharedViewController = [super alloc];
	return sharedViewController;
}

+(id)copy {
	NSAssert(sharedViewController == nil, @"Attempted to copy the singleton");
	return sharedViewController;
}

- (void)didReceiveMemoryWarning {
    [super didReceiveMemoryWarning]; // Releases the view if it doesn't have a superview
    // Release anything that's not essential, such as cached data
}

- (void)dealloc {
    [super dealloc];
}

@end
