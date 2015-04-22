%define kernel  %(uname -r)
%define driver_install_dir /lib/modules/%kernel/extra


Name:           gdrcopy
Version:        1.0
Release:        2
Source0:        %{name}.tar.gz
License:        GPL
Summary:        Nvidia's GPU Direct copy gdrcopy 
Vendor:         Nvidia
Group:          System Environment/Base
AutoReq:        0
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root
Prefix:         /opt/gdrcopy

%description
While GPUDirect RDMA is meant for direct access to GPU memory from third-party devices, it is possible to use these same APIs to create perfectly valid CPU mappings of the GPU memory.
The advantage of a CPU driven copy is the essencially zero latency involved in the copy process. This might be useful when low latencies are required.
Disclaimer
This is just for technology demonstration purposes. In particular this is not an NVIDIA-supported product.
The library relies on a small kernel-mode driver (gdrdrv) which has bug(s) and can even crash your machine. In particular, there is a latent bug related to the concurrent invalidation of mappings and memory deallocation.

%prep
rm -rf $RPM_BUILD_ROOT

%setup -q -n %{name}

%build

make CUDA=/usr/local/cuda-6.5 all


%install

%{__mkdir_p} $RPM_BUILD_ROOT%{prefix}/lib

%{__make} PREFIX=$RPM_BUILD_ROOT%{prefix} lib_install

%{__mkdir_p} $RPM_BUILD_ROOT%{driver_install_dir}

%{__cp}   $RPM_BUILD_DIR/%buildsubdir/gdrdrv/gdrdrv.ko $RPM_BUILD_ROOT/lib/modules/%kernel/extra

install -Dpm 755 copybw $RPM_BUILD_ROOT%{prefix}/bin/copybw
install -Dpm 755 validate $RPM_BUILD_ROOT%{prefix}/bin/validate


%{__mkdir_p} $RPM_BUILD_ROOT/etc/init.d

cat << _EOF_ > $RPM_BUILD_ROOT/etc/init.d/gdrcopy
#!/bin/bash
# 
# gdrcopy    Inserts the gdrcopy driver gdrdrv and creates the gdrdrv device. 
#
# chkconfig: 2345 96 04
# description: A low-latency GPU memory copy library based on NVIDIA GPUDirect RDMA technology 

### BEGIN INIT INFO
# Default-Start: 2 3 4 5
# Default-Stop: 0 1 6
# Short-Description: Setup gdrcopy
#
### END INIT INFO

# Source function library.
. /etc/rc.d/init.d/functions


usage ()
{
    echo "Usage: service \$0 {start|stop}"
    RETVAL=1
}


start ()
{
    #insert driver module
    /sbin/modprobe gdrdrv

    ret=\$?
    
    if [ \$ret -eq  0 ]; then
      # create device inodes
      major=\`fgrep gdrdrv /proc/devices | cut -b 1-4\`

      # remove old inodes just in case
      if [ -e /dev/gdrdrv ]; then
         rm /dev/gdrdrv
      fi

      mknod /dev/gdrdrv c \$major 0
      ret=\$?
      chmod a+w+r /dev/gdrdrv
    fi
    return \$ret
}


stop ()
{

   /sbin/modprobe -r gdrdrv

   # remove old inodes just in case
   if [ -e /dev/gdrdrv ]; then
      rm /dev/gdrdrv
   fi

}    



case "\$1" in
    start) start; RETVAL=\$? ;;
    stop) stop; RETVAL=\$? ;;
    restart) stop; start; RETVAL=\$?;;
    *) usage ; RETVAL=2 ;;
esac

exit \$RETVAL

_EOF_

%{__chmod} 755   $RPM_BUILD_ROOT/etc/init.d/gdrcopy

%clean 
rm -rf $RPM_BUILD_ROOT

%post

/sbin/chkconfig --add gdrcopy
/sbin/depmod

%files
%defattr (-,root,root)
%dir %{prefix}
%{prefix}/*
/etc/init.d/*
%{driver_install_dir}/*
