<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet ekr_test?>
<leo_file>
<leo_header file_format="2" tnodes="0" max_tnode_index="0" clone_windows="0"/>
<globals body_outline_ratio="0.377524143986">
	<global_window_position top="0" left="0" height="709" width="1139"/>
	<global_log_window_position top="0" left="0" height="0" width="0"/>
</globals>
<preferences/>
<find_panel_settings/>
<vnodes>
<v t="loni.20100827184947" a="ETV"><vh>Project</vh>
<v t="loni.20100827184947.1" a="E"><vh>design</vh>
<v t="loni.20100827184947.2"><vh>brainstorming</vh></v>
<v t="loni.20100827184947.3"><vh>objective</vh></v>
<v t="loni.20100827184947.4" a="E"><vh>file/data structure</vh></v>
<v t="loni.20100827184947.5" a="E"><vh>cli syntax</vh></v>
<v t="loni.20100827184947.6"><vh>usage examples</vh></v>
</v>
<v t="loni.20100827184947.7" a="E"><vh>implementation</vh></v>
</v>
</vnodes>
<tnodes>
<t tx="loni.20100827184947">@nocolor
</t>
<t tx="loni.20100827184947.1"></t>
<t tx="loni.20100827184947.2">Q: how do i name this project?

alternatives
    pms (package management system), and you know what else...
    tklps (TurnKey Linux Packaging System)
    spkg (turnkey package ...) - used by slackware
    repoware (repository software)
    poolman (pool management software)
    
A: poolman
    it is the software that manages our pool of packages, see objectives

----

Q: should we have seperate reps per release?
A:  easier to manage
    different toolchain for different releases, poolman also handles the building of packages
    different releases generally mean major updates
    this can be transparent to fab
    smaller global pool, not inifinate in size
    we can retire / archive older release pools
    A: yes

----

Q: what do i call the action/outcome of passing a manifest to poolman?

IDEA: time travel
      a release has a life span, and we can travel forward and backwards on the timeline

action
    travel
    visit
    move
    pluck
    checkout
    peak
    seek
    commit
    make
    generate*
    branch
    
outcome
    instance*
    state
    period
    entity
    frame
    snapshot

latest?
    latest
    present
    head
    current


A: the action is to generate, the outcome is an instance.



</t>
<t tx="loni.20100827184947.3">OBJECTIVE

manage global pool of packages, and generate instances upon request


</t>
<t tx="loni.20100827184947.4">FILE/DATA STRUCTURE

reps/
    &lt;release&gt;/
        params/
            containers
        
        dists/
            &lt;release&gt;/  -&gt; &lt;instance-name-id&gt;
            &lt;instance-name-id&gt;
            &lt;instance-name-id&gt;
            &lt;instance-name-id&gt;

        pool/           -&gt; global | local
                        
        global/         # global pool including all packages
        local/          # local pool used while generating an instance

</t>
<t tx="loni.20100827184947.5">CLI SYNTAX

init release
    initialize a new release pool

register container
    register a package container with the release pool
    container can be:
        /path/to/sumo_arena[#branch]
        /path/to/git_repository[#branch]
        /path/to/regular_directory

unregister container
    unregister a package container from the release pool

generate instance [--component]
    generate new pool instance
    instance can be:
        head                - latest versions containers have to offer
        current             - versions in the current instance
        /path/to/manifest   - according to manifest
    component

info
    show pool information (registered containers, instances, etc.)


            

</t>
<t tx="loni.20100827184947.6">* initialization of rocky instance with latest versions

cd /turnkey/reps
    poolman-init rocky
cd /turnkey/reps/rocky
    poolman-register /turnkey/projects/casper
    poolman-register /turnkey/projects/pristine/rocky
    poolman-register /turnkey/projects/hardened-debs#liraz
    poolman-register /turnkey/projects/backports
    ...
    poolman-generate head

* generate instance from manifest

cd /turnkey/reps/rocky
    poolman-generate /path/to/manifest

* branch current instance to include updated container 

cd /turnkey/reps/rocky
    poolman-generate current --container=/path/to/container


</t>
<t tx="loni.20100827184947.7"></t>
</tnodes>
</leo_file>
