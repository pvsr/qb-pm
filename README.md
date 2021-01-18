# `qpm`: qutebrowser profile manager

[![builds.sr.ht status](https://builds.sr.ht/~pvsr/qpm.svg)](https://builds.sr.ht/~pvsr/qpm?)

qpm is a tool for creating and managing
[qutebrowser](https://github.com/qutebrowser/qutebrowser) profiles. There isn't
any built in concept of profiles in qutebrowser, but there is the `--basedir`
flag which allows you to use any random directory to store qutebrowser config
and data. By default qpm creates profiles that source your main qutebrowser
configuration, but have their own history, bookmarks, etc. Qutebrowser sessions
started from separate profiles are entirely isolated from each other, and can be
opened and closed independently.

## Usage
Create a new profile called "python", edit its `config.py`, then launch it:
```
$ qpm new python
$ qpm edit python
$ qpm launch python docs.python.org
```

Notice that `qpm launch` passes extra arguments directly to qutebrowser, so you
can use it to open urls in your profile and use any options you would pass to
qutebrowser:
```
$ qpm launch python duck.com --target window --loglevel info
```

`qpm from-session` can copy the tabs of a [saved qutebrowser
session](https://qutebrowser.org/doc/help/commands.html#session-save) to a new
profile. If you have a window full of tabs related to planning a vacation, you
could save it to a session called "vacation" using `:session-save -o vacation`
in qutebrowser, then create a new profile with those tabs:
```
$ qpm from-session vacation
```

The default profile directory is `$XDG_DATA_HOME/qutebrowser-profiles`, where
`$XDG_DATA_HOME` is usually `$HOME/.local/share`, but you can create and launch
profiles from anywhere using `--profile-dir`/`-P`:
```
$ qpm --profile-dir ~/dev/my-project new qb-profile
$ cd ~/dev/my-project
$ qpm -P . launch qb-profile
# or
$ qutebrowser --basedir qb-profile
```

## Future ideas that may or may not happen
- Installation instructions
- More shared or copied config and data
- Use any profile as a base for new profiles (currently only the main config in
  `$XDG_CONFIG_HOME` is supported)
- Source `autoconfig.yml` instead of `config.py`
- Bundled config file optimized for single-site browsing
- `qpm.conf` to configure the features above
- Someday: qutebrowser plugin

Patches accepted!
