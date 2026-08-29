df invocation (GNU Coreutils 9.11) Next: du : Estimate file space usage , Up: File space usage [ Contents ][ Index ] 14.1 df : Report file system space usage ¶ df reports the amount of space used and available on
file systems.  Synopsis: df [ option ]... [ file ]... With no arguments, df reports the space used and available on all
currently mounted file systems (of all types).  Otherwise, df reports on the file system containing each argument file . Normally the space is printed in units of
1024 bytes, but this can be overridden (see Block size ).
Non-integer quantities are rounded up to the next higher unit. For bind mounts and without arguments, df only outputs the statistics
for that device with the shortest mount point name in the list of file systems
( mtab ), i.e., it hides duplicate entries, unless the -a option is
specified. With the same logic, df elides a mount entry of a dummy pseudo device
if there is another mount entry of a real block device for that mount point with
the same device number, e.g. the early-boot pseudo file system ‘ rootfs ’ is
not shown per default when already the real root device has been mounted. If an argument file resolves to a special file containing
a mounted file system, df shows the space available on that
file system rather than on the file system containing the device node.
GNU df does not attempt to determine the usage
on unmounted file systems, because on most kinds of systems doing so
requires extremely non-portable intimate knowledge of file system structures. The program accepts the following options.  Also see Common options . ‘ -a ’ ¶ ‘ --all ’ Include in the listing dummy, duplicate, or inaccessible file systems, which
are omitted by default.  Dummy file systems are typically special purpose
pseudo file systems such as ‘ /proc ’, with no associated storage.
Duplicate file systems are local or remote file systems that are mounted
at separate locations in the local file hierarchy, or bind mounted locations.
Inaccessible file systems are those which are mounted but subsequently
over-mounted by another file system at that point, or otherwise inaccessible
due to permissions of the mount point etc. ‘ -B size ’ ¶ ‘ --block-size= size ’ Scale sizes by size before printing them (see Block size ).
For example, -BG prints sizes in units of 1,073,741,824 bytes. ‘ -h ’ ¶ ‘ --human-readable ’ Append a size letter to each size, such as ‘ M ’ for mebibytes.
Powers of 1024 are used, not 1000; ‘ M ’ stands for 1,048,576 bytes.
This option is equivalent to --block-size=human-readable .
Use the --si option if you prefer powers of 1000. ‘ -H ’ ¶ Equivalent to --si . ‘ -i ’ ¶ ‘ --inodes ’ List inode usage information instead of block usage.  An inode (short
for index node) contains information about a file such as its owner,
permissions, timestamps, and location on the file system. ‘ -k ’ ¶ Print sizes in 1024-byte blocks, overriding the default block size
(see Block size ).
This option is equivalent to --block-size=1K . ‘ -l ’ ¶ ‘ --local ’ Limit the listing to local file systems.  By default, remote file systems
are also listed. ‘ --no-sync ’ ¶ Do not invoke the sync system call before getting any usage data.
This may make df run significantly faster on systems with many
file systems, but on some systems (notably Solaris) the results may be slightly
out of date.  This is the default. ‘ --output[= field_list ] ’ ¶ Use the output format defined by field_list , or print all fields if field_list is omitted.  In the latter case, the order of the columns
conforms to the order of the field descriptions below. The use of the --output together with each of the options -i , -P , and -T is mutually exclusive. FIELD_LIST is a comma-separated list of columns to be included in df ’s
output and therefore effectively controls the order of output columns.
Each field can thus be used at the place of choice, but yet must only be
used once. Valid field names in the field_list are: ‘ source ’ The source of the mount point, usually a device. ‘ fstype ’ File system type. ‘ itotal ’ Total number of inodes. ‘ iused ’ Number of used inodes. ‘ iavail ’ Number of available inodes. ‘ ipcent ’ Percentage of iused divided by itotal . ‘ size ’ Total number of blocks. ‘ used ’ Number of used blocks. ‘ avail ’ Number of available blocks. ‘ pcent ’ Percentage of used divided by size . ‘ file ’ The file name if specified on the command line. ‘ target ’ The mount point. The fields for block and inodes statistics are affected by the scaling
options like -h as usual. The definition of the field_list can even be split among several --output uses. #!/bin/sh
# Print the TARGET (i.e., the mount point) along with their percentage
# statistic regarding the blocks and the inodes.
df --out=target --output=pcent,ipcent

# Print all available fields.
df --o ‘ -P ’ ¶ ‘ --portability ’ Use the POSIX output format.  This is like the default format except
for the following: The information about each file system is always printed on exactly
one line; a mount device is never put on a line by itself.  This means
that if the mount device name is more than 20 characters long (e.g., for
some network mounts), the columns are misaligned. The labels in the header output line are changed to conform to POSIX. The default block size and output format are unaffected by the DF_BLOCK_SIZE , BLOCK_SIZE and BLOCKSIZE environment
variables.  However, the default block size is still affected by POSIXLY_CORRECT : it is 512 if POSIXLY_CORRECT is set, 1024
otherwise.  See Block size . ‘ --si ’ ¶ Append an SI-style abbreviation to each size, such as ‘ M ’ for
megabytes.  Powers of 1000 are used, not 1024; ‘ M ’ stands for
1,000,000 bytes.  This option is equivalent to --block-size=si .  Use the -h or --human-readable option if
you prefer powers of 1024. ‘ --sync ’ ¶ Invoke the sync system call before getting any usage data.  On
some systems (notably Solaris), doing this yields more up to date results,
but in general this option makes df much slower, especially when
there are many or very busy file systems. ‘ --total ’ ¶ Print a grand total of all arguments after all arguments have
been processed.  This can be used to find out the total size, usage
and available space of all listed devices.  If no arguments are specified
df will try harder to elide file systems insignificant to the total
available space, by suppressing duplicate remote file systems. For the grand total line, df prints ‘ total ’ into the source column, and ‘ - ’ into the target column.
If there is no source column (see --output ), then df prints ‘ total ’ into the target column,
if present. ‘ -t fstype ’ ¶ ‘ --type= fstype ’ Limit the listing to file systems of type fstype .  Multiple
file system types can be specified by giving multiple -t options.
By default, nothing is omitted. ‘ -T ’ ¶ ‘ --print-type ’ Print each file system’s type.  The types printed here are the same ones
you can include or exclude with -t and -x .  The particular
types printed are whatever is supported by the system.  Here are some of
the common names (this list is certainly not exhaustive): ‘ nfs ’ ¶ An NFS file system, i.e., one mounted over a network from another
machine.  This is the one type name which seems to be used uniformly by
all systems. ‘ ext2 , ext3 , ext4 , xfs , btrfs… ’ ¶ A file system on a locally-mounted device.  (The system might even
support more than one type here; GNU/Linux does.) ‘ iso9660 , cdfs ’ ¶ A file system on a CD or DVD drive.  HP-UX uses ‘ cdfs ’, most other
systems use ‘ iso9660 ’. ‘ ntfs , fat ’ ¶ File systems used by MS-Windows / MS-DOS. ‘ -x fstype ’ ¶ ‘ --exclude-type= fstype ’ Limit the listing to file systems not of type fstype .
Multiple file system types can be eliminated by giving multiple -x options.  By default, no file system types are omitted. ‘ -v ’ ¶ Ignored; for compatibility with System V versions of df . df is installed only on systems that have usable mount tables,
so portable scripts should not rely on its existence. An exit status of zero indicates success,
and a nonzero value indicates failure.
Failure includes the case where no output is generated, so you can
inspect the exit status of a command like ‘ df -t ext3 -t reiserfs dir ’ to test whether dir is on a file system of type
‘ ext3 ’ or ‘ reiserfs ’. Since the list of file systems ( mtab ) is needed to determine the
file system type, failure includes the cases when that list cannot
be read and one or more of the options -a , -l , -t or -x is used together with a file name argument. Next: du : Estimate file space usage , Up: File space usage [ Contents ][ Index ]