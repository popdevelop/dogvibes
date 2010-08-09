//
//  FirstViewController.h
//  iDog
//
//  Created by Johan Nyström on 2009-05-26.
//  Copyright NoName 2009. All rights reserved.
//

#import <UIKit/UIKit.h>

@interface FirstViewController : UIViewController {
	IBOutlet UIButton *playButton;
	IBOutlet UIButton *nextButton;
	IBOutlet UIButton *prevButton;
	IBOutlet UIButton *stopButton;
	IBOutlet UISlider *volumeSlider;
	IBOutlet UIImageView *jsonImage;
	IBOutlet UILabel *label;
	int state;
	int visitCount;
}

- (IBAction)playButtonPressed:(id)sender;
- (IBAction)stopButtonPressed:(id)sender;
- (IBAction)nextButtonPressed:(id)sender;
- (IBAction)prevButtonPressed:(id)sender;
- (IBAction)volumeChanged:(id)sender;

- (void)setPlayButtonImage:(UIImage *)image;
- (void)updateTrackInfo;
- (void)check_system_prefs;
@end
