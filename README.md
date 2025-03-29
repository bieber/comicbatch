This is a quick and dirty script to split a directory full of CBZ
comics into PDF volumes less than a given file size, scaled to fit
your desired device screen size.  All the defaults are set to play
nice with the Remarkable Paper Pro, but you can adjust them to your
liking.  Just run it with -h for the full list of command line
arguments.

Note that this will create and delete a /tmp subdirectory in the
directory you run it in, so make sure you don't have anything you want
to keep there.

This is a pure Python script, but it does require that Imagemagick and
img2pdf are installed and available on the path as it shells out to
those for image scaling and compilation.  It will also probably break
if you have quotation marks in your file paths, sorry, I didn't get
around to setting up proper escaping.
