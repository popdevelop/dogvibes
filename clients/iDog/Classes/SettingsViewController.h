//
//  SettingsViewController.h
//  iDog
//
//  Created by Johan Nyström on 2009-05-26.
//  Copyright 2009 NoName. All rights reserved.
//

#import <UIKit/UIKit.h>

@interface SettingsViewController : UIViewController <UITextFieldDelegate>{
	/* gui components */
	IBOutlet UITextField *IPtextField;
	IBOutlet UILabel *label;
	IBOutlet UIButton *statusBtn;
	IBOutlet UITextView *textView;
	IBOutlet UISwitch *spk0;
	IBOutlet UISwitch *spk1;
	IBOutlet UISwitch *spk2;
}

/* button handlers */
- (IBAction)statusButtonPressed:(id)sender;

/* slider handlers */
- (IBAction)slider0Changed:(id)sender;
- (IBAction)slider1Changed:(id)sender;
- (IBAction)slider2Changed:(id)sender;

/* textfield handlers */
- (IBAction)IPtextFieldChanged:(id)sender;

- (NSString *)getIPfromTextField;
- (void)setIPTextField:(NSString *)text;

/* export the settingsviewcontroller */
+(SettingsViewController *) sharedViewController;

@end
