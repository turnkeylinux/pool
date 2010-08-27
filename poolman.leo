<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet ekr_test?>
<leo_file>
<leo_header file_format="2" tnodes="0" max_tnode_index="0" clone_windows="0"/>
<globals body_outline_ratio="0.5">
	<global_window_position top="0" left="210" height="600" width="800"/>
	<global_log_window_position top="0" left="0" height="0" width="0"/>
</globals>
<preferences/>
<find_panel_settings/>
<vnodes>
<v t="loni.20100827184506" a="E"><vh>Project</vh>
<v t="loni.20100827184506.1" a="E"><vh>design</vh>
<v t="loni.20100827184506.2" a="V"><vh>names</vh></v>
<v t="loni.20100827184506.3"><vh>background</vh></v>
<v t="loni.20100827184506.4"><vh>objective</vh></v>
<v t="loni.20100827184506.5"><vh>package types</vh></v>
<v t="loni.20100827184506.6"><vh>package actions</vh></v>
<v t="loni.20100827184506.7" a="E"><vh>file/data structure</vh></v>
<v t="loni.20100827184506.9"><vh>cli syntax</vh></v>
</v>
<v t="loni.20100827184506.10" a="E"><vh>implementation</vh></v>
</v>
</vnodes>
<tnodes>
<t tx="loni.20100827184506">@nocolor
</t>
<t tx="loni.20100827184506.1"></t>
<t tx="loni.20100827184506.2">Q: how do i name this project?

alternatives
    pms (package management system), and you know what else...
    tklps (TurnKey Linux Packaging System)
    spkg (turnkey package ...) - used by slackware
 </t>
<t tx="loni.20100827184506.3">BACKGROUND

There are 5 basic package related actions: import, fork, build, store, share.
Currently we dont have an organized package managment system, and are using make-shift scripts spanning over several projects, with no real structure.
eg.
* import: world-evaluate and world-import
* fork:   manually (ok for small forks, need sumo for large forks)
* build:  fab-package needing pkginfo file in project source
* store:  repo-init (fab/bin), fab-package with update option, world-import
* share:  world-exports and world-update, covin

There are lots of downsides to our current setup, but lets focus on the future...</t>
<t tx="loni.20100827184506.4">OBJECTIVES

* consolate package related activity under 1 roof
* don't impose rules on users relating to directory structure, project development, etc.
  its a matter of style, preference, judgment...
* package repository "instances"
  allow for different repositories to be worked on concurrently without mixing and messing
  not just a dumb heirarchy of debs
  instead of pushing to repository, let repository pull
* repository data should not be in packages, but in the repository/package management software
* leverage sumo for public data set sharing</t>
<t tx="loni.20100827184506.5">PACKAGE TYPES

There are 3 different types of packages:
    * pristine | vanilla: pure untouched upstream deb imports
    * forked   | world:   any upstream package we have changed or rebuilt (ie. not pristine)
    * private:            our privately developed projects</t>
<t tx="loni.20100827184506.6">PACKAGE ACTIONS

* import (pristine packages)
    leverage sumo arena to manage the public data sets
    seperate arena for each release, allows flexability such as parallel release development
    manual import via sumo-get
    auto import via package management software (similar to world-evaluate and world-import)
    use softlink from repository component to arena
        eg. reps/&lt;release&gt;/pool/pristine -&gt; pristine/&lt;release&gt;/arena

* store
    have multiple repositories, configurable by user
    seperate rep for each release, allows flexability such as parallel release development
    not dumb hierarchy, configurable
    ability to pull debs not only get pushed them

* fork
    user decides how to fork a package, but we should provide guidelines.
        small package source, major changes - preferable not to arena
            branches, full git functionality, upstream source change tracking, etc...
            eg. casper
        large package source, small changes - preferable to use arena
            eg. mozilla-firefox
    recompiles are considered forks
        its up to the user to decide if he wants to patch it or not
        it might be a small backport, get source, build, register deb
            it might be a massive backport that we do update the control file to just build X 

    large forks debs should be made available
    
    
* build
    intelligent package management software, user configurable
        decked chroot
        auto-import build dependencies
        figure out if project source, arena, deb imports, ...
        arena sources shouldn't be built automatically?
            kernel, firefox, etc.
                major deps, long build time, source access control, etc.
                    the maintainer should provide a deb
        registered packages/projects in rep

* share
    all package types are shared over covin (leveraging sumo where applicable)</t>
<t tx="loni.20100827184506.7">FILE/DATA STRUCTURE

reps/
    &lt;release&gt;/
        params/
            specs            
        dists/
        pool/
            &lt;component_link&gt;/
            &lt;component&gt;/
            &lt;component&gt;/


pristine/
    &lt;release&gt;/
        params/
            upstream-release
            upstream-mirror
            upstream-components


.&lt;project_name&gt;/
    cache/




</t>
<t tx="loni.20100827184506.9">CLI SYNTAX

init &lt;release&gt;
    initialize a repository release in cwd

register [options] /path/to/register
    recursive (path is a directory of projects)
    component (path is a directory of debs, eg. pristine, backports)

ignore /path/to/ignore
    directory to ignore if recursive directory is registered)
        
unregister /path/to/unregister

index
    index the repository

import &lt;package&gt;
    import a package

build [options] [project] [project] ...
    build project(s) and optionally update the repository

        
</t>
<t tx="loni.20100827184506.10"></t>
</tnodes>
</leo_file>
