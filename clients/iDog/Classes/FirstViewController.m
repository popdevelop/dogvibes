//
//  FirstViewController.m
//  iDog
//
//  Created by Johan Nyström on 2009-05-26.
//  Copyright NoName 2009. All rights reserved.
//

#import "FirstViewController.h"
#import "SettingsViewController.h"
#import "iDogAppDelegate.h"
#import "DogUtils.h"
#import "JSON.h"

@implementation FirstViewController

// Implement viewDidLoad to do additional setup after loading the view, typically from a nib.
- (void)viewDidLoad {
    [super viewDidLoad];
	[self check_system_prefs];
	
	/* load album art */
	UIImage *img = [UIImage alloc];
	iDogAppDelegate *appDelegate = (iDogAppDelegate *)[[UIApplication sharedApplication] delegate];
	DogUtils *dog = [[DogUtils alloc] init];
	
	if (visitCount != 0) {

		NSString *jsonData = [NSString alloc];
		jsonData = [dog dogRequest:@"/amp/0/getStatus"];

		if (jsonData == nil) {
			UIAlertView *alert = [[UIAlertView alloc] 
								  initWithTitle:@"No reply from server!"   \
								  message:@"Either the webservice is down  \
								  (verify with Statusbutton under setting) \
								  or else there's nothing added in playlist."  
								  delegate:self cancelButtonTitle:@"OK" 
								  otherButtonTitles: nil];
			[alert show];
			[alert release];
		} else {
			NSDictionary *trackDict = [jsonData JSONValue];
			NSDictionary *result = [trackDict objectForKey:@"result"];
			NSString *playState = [NSString stringWithFormat:@"%@",[result objectForKey:@"state"], nil];
			
			if ([playState compare:@"playing"] == 0) {
				[self setPlayButtonImage:[UIImage imageNamed:@"pause.png"]];
			} else if (playState){
				[self setPlayButtonImage:[UIImage imageNamed:@"play.png"]];
			}
			
			NSLog(@"new track: %@   curTrack: %@ ", (NSString *)[result objectForKey:@"uri"], [appDelegate getCurTrack]);
			
			if ([(NSString *)[result objectForKey:@"uri"] compare:[appDelegate getCurTrack]] != 0) {
				/* only request image if we need.. */
				img = [dog dogGetAlbumArt:[result objectForKey:@"uri"]];
				NSLog(@"Update album art..");
				jsonImage.image = [img retain];			
			} else {
				NSLog(@"same song as last time...");
			}

			label.text = [NSString stringWithFormat:@"%@ - %@", [result objectForKey:@"title"], [result objectForKey:@"album"], nil];
			[appDelegate setCurTrack:(NSString *)[result objectForKey:@"uri"]];
		}
	}
		
	visitCount++;
	
	[img release];
	[dog release];
}

- (void)setPlayButtonImage:(UIImage *)image
{
	[playButton setImage:image forState:0];
}

- (IBAction)playButtonPressed:(id)sender
{
	DogUtils *dog = [[DogUtils alloc] init];
	NSString *jsonData = [NSString alloc];
	
	/* update button */
	if (state != 1) {
		jsonData = [dog dogRequest:@"/amp/0/play"];
		state = 1;
		[self setPlayButtonImage:[UIImage imageNamed:@"pause.png"]];
		NSLog(@"switching to state %d ", state);
	} else {
		jsonData = [dog dogRequest:@"/amp/0/pause"];
		state = 0;
		[self setPlayButtonImage:[UIImage imageNamed:@"play.png"]];
		NSLog(@"switching to state %d ", state);
	}
	
	[dog release];
	/* refresh album and track title */
	[self updateTrackInfo];	
}

- (IBAction)prevButtonPressed:(id)sender
{
	DogUtils *dog = [[DogUtils alloc] init];
	NSString *jsonData = [NSString alloc];
	jsonData = [dog dogRequest:@"/amp/0/previousTrack"];
	[dog release];
	[self updateTrackInfo];
}

- (IBAction)stopButtonPressed:(id)sender
{
	DogUtils *dog = [[DogUtils alloc] init];
	NSString *jsonData = [NSString alloc];
	jsonData = [dog dogRequest:@"/amp/0/stop"];
	[dog release];
}

- (IBAction)nextButtonPressed:(id)sender
{
	DogUtils *dog = [[DogUtils alloc] init];
	NSString *jsonData = [NSString alloc];
	jsonData = [dog dogRequest:@"/amp/0/nextTrack"];
	[dog release];
	[self updateTrackInfo];
}

- (void) updateTrackInfo {
	DogUtils *dog = [[DogUtils alloc] init];
	NSString *jsonData = [NSString alloc];
	jsonData = [dog dogRequest:@"/amp/0/getStatus"];
	UIImage *img = [UIImage alloc];
	iDogAppDelegate *appDelegate = (iDogAppDelegate *)[[UIApplication sharedApplication] delegate];
		
	if (jsonData == nil) {
		UIAlertView *alert = [[UIAlertView alloc] initWithTitle:@"No reply from server!" message:@"Either the webservice is down (verify with Statusbutton under setting) or else, there's nothing added in playlist."  delegate:self cancelButtonTitle:@"OK" otherButtonTitles: nil];
		[alert show];
		[alert release];
	} else {
		NSDictionary *trackDict = [jsonData JSONValue];
		NSDictionary *result = [trackDict objectForKey:@"result"];
		label.text = [NSString stringWithFormat:@"%@ - %@", [result objectForKey:@"title"], [result objectForKey:@"album"], nil];
		if ([(NSString *)[result objectForKey:@"uri"] compare:[appDelegate getCurTrack]] != 0) {
			/* only request image if we need.. */
			img = [dog dogGetAlbumArt:[result objectForKey:@"uri"]];
			NSLog(@"Update album art..");
			jsonImage.image = [img retain];			
		} else {
			NSLog(@"same song as last time...");
		}
		[appDelegate setCurTrack:(NSString *)[result objectForKey:@"uri"]];		
	}
	[dog release];
}

- (IBAction) volumeChanged:(id)sender
{
	UISlider *mySlider = (UISlider *) sender;
	DogUtils *dog = [[DogUtils alloc] init];
	NSString *jsonData = [NSString alloc];
	jsonData = [dog dogRequest:[NSString stringWithFormat:@"/amp/0/setVolume?level=%f",mySlider.value, nil]];
	[dog release];
}

- (void) check_system_prefs {
	iDogAppDelegate *iDogApp = (iDogAppDelegate *)[[UIApplication sharedApplication] delegate];
	iDogApp.kDogVibesIP = @"dogVibesIP";
	NSString *testValue = [[NSUserDefaults standardUserDefaults] stringForKey:iDogApp.kDogVibesIP];
	NSLog(@"trying to fetch ip from db ip:%@ ", testValue);
	if (testValue == nil)
	{
		// no default values have been set, create them here based on what's in our Settings bundle info
		//
		NSString *pathStr = [[NSBundle mainBundle] bundlePath];
		NSString *settingsBundlePath = [pathStr stringByAppendingPathComponent:@"Settings.bundle"];
		NSString *finalPath = [settingsBundlePath stringByAppendingPathComponent:@"Root.plist"];
		
		NSDictionary *settingsDict = [NSDictionary dictionaryWithContentsOfFile:finalPath];
		NSArray *prefSpecifierArray = [settingsDict objectForKey:@"PreferenceSpecifiers"];
		
		NSString *dogVibesIPDefault;		
		NSDictionary *prefItem;
		
		for (prefItem in prefSpecifierArray)
		{
			NSString *keyValueStr = [prefItem objectForKey:@"Key"];
			id defaultValue = [prefItem objectForKey:@"DefaultValue"];
			
			if ([keyValueStr isEqualToString:iDogApp.kDogVibesIP])
			{
				dogVibesIPDefault = defaultValue;
			}
			
		}
		
		// since no default values have been set (i.e. no preferences file created), create it here		
		NSDictionary *appDefaults = [NSDictionary dictionaryWithObjectsAndKeys:
									 dogVibesIPDefault, iDogApp.kDogVibesIP,
									 nil];
		[[NSUserDefaults standardUserDefaults] registerDefaults:appDefaults];
		[[NSUserDefaults standardUserDefaults] synchronize];
	}
	
	// we're ready to do, so lastly set the key preference values
	iDogApp.dogIP = [[NSUserDefaults standardUserDefaults] stringForKey:iDogApp.kDogVibesIP];
	NSLog(@"done getting ip from db.. ");
}

- (void)didReceiveMemoryWarning {
    [super didReceiveMemoryWarning]; // Releases the view if it doesn't have a superview
    // Release anything that's not essential, such as cached data
}

- (void)dealloc {
    [super dealloc];
}

@end
