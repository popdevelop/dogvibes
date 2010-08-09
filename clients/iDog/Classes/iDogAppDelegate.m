//
//  iDogAppDelegate.m
//  iDog
//
//  Created by Johan Nyström on 2009-05-26.
//  Copyright NoName 2009. All rights reserved.
//

#import "iDogAppDelegate.h"

@implementation iDogAppDelegate

@synthesize window;
@synthesize tabBarController;
@synthesize navController;
@synthesize curTrack;
@synthesize dogIP, kDogVibesIP;

- (void)applicationDidFinishLaunching:(UIApplication *)application {
	NSLog(@"appFinishedLaunching...");
    // Add the tab bar controller's current view as a subview of the window
    [window addSubview:tabBarController.view];
}

// Optional UITabBarControllerDelegate method
- (void)tabBarController:(UITabBarController *)tabBarController didSelectViewController:(UIViewController *)viewController {
	NSLog(@"didSelectViewController...");
	[viewController viewDidLoad];
}

- (NSString*) getCurTrack {
	NSLog(@"cur track is: %@ ", self.curTrack);
	return curTrack;
}

- (void) setCurTrack:(NSString *)uri {
	NSLog(@"cur track updated to: %@ ", uri);
	[curTrack autorelease];
	curTrack = [uri retain];
}

- (void)dealloc {
    [tabBarController release];
    [window release];
    [super dealloc];
}

@end
