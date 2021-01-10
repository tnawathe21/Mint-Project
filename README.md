# Mint-Project
Follow these instructions to get DailyMint running on your computer:

## __1. Install dependencies__
	
  You will need to download the following packages for DailyMint:

  * mintapi
  * yagmail
  * keyring
  * pandas

  The easiest way to install these dependencies is to download [anaconda](https://www.anaconda.com/products/individual). You could also `pip install` these packages.

## __2. Download files__
Download these files into your IDE:

  * DailyMint.py
  * email_template.html
  * run_DailyMint.sh
	
## __3. Configure gmail settings to send an email from a gmail account__
	
<<<<<<< HEAD
  You will need to adjust your google account settings to be able to use `yagmail` to send an an automated email through your account.
=======
  You will need to adjust your google account settings to be able to use `yagmail` to send an automated email through your account.
>>>>>>> b8cef7946fe1ed610feef8647214c8f4d2bc3a99
  
  Click on the account icon on the top right corner of your gmail account. Click __Manage > Security__. Navigate to the __Less secure app access__ section. Use the toggle switch to enable less secure apps.

## __4. Run setup__

In your command line tool, run `python DailyMint.py`. This will give you a list of ways to run the program. 

For the setup, run `python DailyMint.py setup`. This will securely store your Mint and gmail account information using `keyring` so you will not have to re-enter that information when you run the program again.

## __5. Run the program__
Now that your credentials have been stored in keyring, you can run `python DailyMint.py myemail@xyz.com` replacing myemail@xyz.com with your email address. There will be some output on your command line prompt as the program executes. 
  
  After the program has finished running, you should see that you have received an email on your google account. A few csv files should also have been created. These files are a record of your accounts, account history, and transactions.

## __6. Schedule a cron job for daily email__
In the files given, __run_DailyMint.sh__ is a shell script that you will execute to run your program at a scheduled time. Type `chmod +x run_DailyMint.sh` to make the script executable.

To get a daily email, you will need to program the shell script to run using crontab. Type `crontab -e`. You are now in the file that stores all of your cron jobs. 

Press ___i___ to enter Insert mode. Type `0 0 * * * path/to/your/file/run_DailyMint.sh`. This indicates that cron will execute __run_DailyMint.sh__ every day at midnight. Here is some [info](https://crontab.guru/) on crontab syntax in case you would like to personalize your cron job.

Press ___esc___ to exit Insert mode. Type `:wq` to save and quit the text editor.

___Note:___ If you notice that your cron job is not running on your mac, this may be because of security settings. Go to __Settings > Security & Privacy > Privacy > Full Disk Access__. Click the lock at the bottom left corner to make changes. You will need to add `cron` as an application with full disk access. To do so, find where `cron` is located on your computer. This might be in `/bin`, `/sbin`, or `/usr/sbin`. Open these directories (you can type `open /sbin` in the terminal, for example) and search for `cron`. Drag it into the full disk access list and check the box to give it full disk access. Click the lock again to lock in your changes. You may have to enter your mac password. Now cron should have the proper permissions to run.



