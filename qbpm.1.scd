qbpm(1)

# NAME

qbpm - qutebrowser profile manager

# SYNOPSIS

*qbpm* [--profile-dir=<path>|-P <path>] <command> [<args>]

# DESCRIPTION

qbpm is a tool for creating and running qutebrowser profiles. qutebrowser
doesn't have a native concept of profiles, but it does have a --basedir flag
that allows qutebrowser's config, cache, and data to be stored in any directory.
So a profile is simply a directory meant to be set as qutebrowser's basedir.
qbpm creates profiles that source the config.py from your qutebrowser config dir
in $XDG_CONFIG_HOME (typically $HOME/.config/qutebrowser). By default profiles
are stored in a qutebrowser-profiles/ dir in $XDG_DATA_HOME (typically
$HOME/.local/share), but this can be set to another directory by passing
\--profile-dir to qbpm or setting the $QBPM_PROFILE_DIR environment variable.

# OPTIONS

*-h, --help*
	Show help message and quit.

*--version*
	Show version information and quit.

*-P, --profile-dir* <path>
	Use _path_ as the profile directory instead of the default location. Takes
	precedence over the QBPM_PROFILE_DIR environment variable.

*-C, --config-dir*
	Source config files from the provided directory instead of the global
	qutebrowser config location.

# COMMANDS

*new* [options] <profile> [<url>]
	Create a new qutebrowser profile named _profile_. If _url_ is present it will
	be used as the profile's home page. By default, a .desktop file will be
	created for the profile in $XDG_DATA_HOME/applications/qbpm/.

	Options:

	*-l, --launch*
		Launch the profile after it is created.

	*-f, --foreground*
		If --launch is set, run qutebrowser in the foreground.

	*--no-desktop-file*
		Do not generate a .desktop file for the profile.

	*--overwrite*
		By default qbpm will refuse to create a profile if one with the same name
		already exists. --overwrite disables this check and rewrites the existing
		profile's configuration files from scratch. Profile data is left untouched.

*launch* [options] <profile> [argument...]
	Start qutebrowser with --basedir set to the location of _profile_. All
	arguments following _profile_ will be passed on to qutebrowser.

	Options:

	*-f, --foreground*
		Run qutebrowser in the foreground instead of forking off a new process.

	*-c, --create*
		Create the profile if it does not exist.

	Examples:

		```
		\# launch my profile called work and open internal.mycompany.com
		qbpm launch work internal.mycompany.com

		\# launch a new profile called qb-dev, passing the flags to qutebrowser
		qbpm launch -n qb-dev --debug --json-logging
		```

*icon* [options] <profile> <icon>
	Install an icon to _profile_. _icon_ may be a url, a path to an image file,
	or, if --by-name is passed, the name of an xdg icon installed on your
	system. If _icon_ is a url, qbpm will fetch the page and attempt to find a
	suitable favicon.

	Options:

	*-n, --by-name*
		Interpret _icon_ as the name of an xdg icon file according to the
		freedesktop.org icon specification. Likely to only work on Linux.

*choose* [options]
	Open a menu to choose a qutebrowser profile to launch. On linux this defaults
	to dmenu or another compatible menu program such as rofi, and on macOS this
	will be an applescript dialog.

	*-m, --menu* <menu>
		Use _menu_ instead of the default menu program. This may be the name of a
		program on $PATH or a path to a program, in which case it will be run in
		dmenu mode if qbpm knows about the program, or a full command line.

	Examples:

		```
		\# runs "echo {profiles} | /path/to/rofi -dmenu -no-custom -p qutebrowser"
		qbpm choose -m /path/to/rofi

		qbpm choose -m "my-cool-menu --dmenu-mode --prompt qutebrowser"
		```

*from-session* [options] <session> [<name>]
	Create a new qutebrowser profile from _session_, which may either be the name
	of a session in the default qutebrowser data directory, or a path to a session
	file. By default the new profile will be named after _session_, but a custom
	profile name can be set via the _name_ argument. Supports the same options as
	*new*.

*desktop* <profile>
	Generate a .desktop file for _profile_.

*edit* <profile>
	Open _profile_'s config.py in your default editor.

*list*
	List qutebrowser profiles.

# AUTHOR

Peter Rice

# CONTRIBUTE

_https://github.com/pvsr/qbpm_

_https://codeberg.org/pvsr/qbpm_

# LICENSE

src/qbpm/favicon.py: MIT

all other code and qbpm as a whole: GPLv3+
