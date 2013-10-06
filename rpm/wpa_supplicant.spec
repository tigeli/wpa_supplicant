Name:       wpa_supplicant

Summary:    WPA/WPA2/IEEE 802.1X Supplicant
Version:    2.0
Release:    1
Group:      System Environment/Base
License:    GPLv2
URL:        http://w1.fi/wpa_supplicant/
Source0:    %{name}-%{version}.tar.gz
Source1:    build-config
Source2:    %{name}.conf
Source3:    %{name}.service
Source4:    %{name}.sysconfig
Source5:    %{name}.logrotate
Source6:    wpa_supplicant-2.0-generate-libeap-peer.patch
Patch0:     wpa_supplicant-assoc-timeout.patch
Patch1:     wpa_supplicant-flush-debug-output.patch
Patch2:     wpa_supplicant-dbus-service-file-args.patch
Patch3:     wpa_supplicant-quiet-scan-results-message.patch
Patch4:     wpa_supplicant-openssl-more-algs.patch
Patch5:     wpa_supplicant-gui-qt4.patch
Patch6:     libnl3-includes.patch
BuildRequires:  pkgconfig(libnl-3.0)
BuildRequires:  pkgconfig(dbus-1)
BuildRequires:  pkgconfig(openssl)
BuildRequires:  readline-devel

%description
wpa_supplicant is a WPA Supplicant for Linux, BSD and Windows with support
for WPA and WPA2 (IEEE 802.11i / RSN). Supplicant is the IEEE 802.1X/WPA
component that is used in the client stations. It implements key negotiation
with a WPA Authenticator and it controls the roaming and IEEE 802.11
authentication/association of the wlan driver.


%package -n libeap-devel
Summary:    Header files for EAP peer library
Group:      Development/Libraries
Requires:   %{name} = %{version}-%{release}
Requires:   libeap = %{version}-%{release}

%description -n libeap-devel
This package contains header files for using the EAP peer library.
Don't use this unless you know what you're doing.


%package -n libeap
Summary:    EAP peer library
Group:      System Environment/Libraries
Requires:   %{name} = %{version}-%{release}
Requires(post): /sbin/ldconfig
Requires(postun): /sbin/ldconfig

%description -n libeap
This package contains the runtime EAP peer library. Don't use this
unless you know what you're doing.


%prep
%setup -q -n %{name}-%{version}/hostap

# wpa_supplicant-assoc-timeout.patch
%patch0 -p1
# wpa_supplicant-flush-debug-output.patch
%patch1 -p1
# wpa_supplicant-dbus-service-file-args.patch
%patch2 -p1
# wpa_supplicant-quiet-scan-results-message.patch
%patch3 -p1
# wpa_supplicant-openssl-more-algs.patch
%patch4 -p1
# wpa_supplicant-gui-qt4.patch
%patch5 -p1
# libnl3-includes.patch
%patch6 -p1

%build
pushd wpa_supplicant
cp %{SOURCE1} .config
CFLAGS="${CFLAGS:-%optflags}" ; export CFLAGS ;
CXXFLAGS="${CXXFLAGS:-%optflags}" ; export CXXFLAGS ;
# yes, BINDIR=_sbindir
BINDIR="%{_sbindir}" ; export BINDIR ;
LIBDIR="%{_libdir}" ; export LIBDIR ;
make %{?jobs:-j%jobs}
popd

%install
rm -rf %{buildroot}

# init scripts
install -D -m 0755 %{SOURCE3} %{buildroot}/%{_lib}/systemd/system/%{name}.service
install -D -m 0644 %{SOURCE4} %{buildroot}/%{_sysconfdir}/sysconfig/%{name}
install -D -m 0644 %{SOURCE5} %{buildroot}/%{_sysconfdir}/logrotate.d/%{name}

# config
install -D -m 0600 %{SOURCE2} %{buildroot}/%{_sysconfdir}/%{name}/%{name}.conf

# binary
install -d %{buildroot}/%{_sbindir}
install -m 0755 %{name}/wpa_passphrase %{buildroot}/%{_sbindir}
install -m 0755 %{name}/wpa_cli %{buildroot}/%{_sbindir}
install -m 0755 %{name}/wpa_supplicant %{buildroot}/%{_sbindir}
install -D -m 0644 %{name}/dbus/dbus-wpa_supplicant.conf %{buildroot}/%{_sysconfdir}/dbus-1/system.d/wpa_supplicant.conf
install -D -m 0644 %{name}/dbus/fi.w1.wpa_supplicant1.service %{buildroot}/%{_datadir}/dbus-1/system-services/fi.w1.wpa_supplicant1.service
install -D -m 0644 %{name}/dbus/fi.epitest.hostap.WPASupplicant.service %{buildroot}/%{_datadir}/dbus-1/system-services/fi.epitest.hostap.WPASupplicant.service

# running
mkdir -p %{buildroot}/%{_localstatedir}/run/%{name}

# man pages
#install -d %{buildroot}%{_mandir}/man{5,8}
#install -m 0644 %{name}/doc/docbook/*.8 %{buildroot}%{_mandir}/man8
#install -m 0644 %{name}/doc/docbook/*.5 %{buildroot}%{_mandir}/man5

# some cleanup in docs and examples
rm -f  %{name}/doc/.cvsignore
rm -rf %{name}/doc/docbook
chmod -R 0644 %{name}/examples/*.py

# HAAACK
patch -p1 -b --suffix .wimax < %{SOURCE6}
pushd wpa_supplicant
make clean
make -C ../src/eap_peer
make DESTDIR=%{buildroot} LIB=%{_lib} -C ../src/eap_peer install
sed -i -e 's|libdir=/usr/lib|libdir=%{_libdir}|g' %{buildroot}/%{_libdir}/pkgconfig/*.pc
popd

%preun
if [ $1 -eq 0 ] ; then
# Package removal, not upgrade
/bin/systemctl --no-reload disable wpa_supplicant.service > /dev/null 2>&1 || :
/bin/systemctl stop wpa_supplicant.service > /dev/null 2>&1 || :
fi

%post
if [ $1 -eq 1 ] ; then
# Initial installation
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
fi

%postun
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
# Lets not restart wpa_supplicant on postun to make sure network connectivity is not
# broken during update process.

%post -n libeap -p /sbin/ldconfig

%postun -n libeap -p /sbin/ldconfig

%files
%defattr(-,root,root,-)
%doc COPYING %{name}/ChangeLog README %{name}/eap_testing.txt %{name}/todo.txt %{name}/wpa_supplicant.conf %{name}/examples
%config(noreplace) %{_sysconfdir}/%{name}/%{name}.conf
%config(noreplace) %{_sysconfdir}/sysconfig/%{name}
%config(noreplace) %{_sysconfdir}/logrotate.d/%{name}
/%{_lib}/systemd/system/%{name}.service
%{_sysconfdir}/dbus-1/system.d/%{name}.conf
%{_datadir}/dbus-1/system-services/fi.epitest.hostap.WPASupplicant.service
%{_datadir}/dbus-1/system-services/fi.w1.wpa_supplicant1.service
%{_sbindir}/wpa_passphrase
%{_sbindir}/wpa_supplicant
%{_sbindir}/wpa_cli
%dir %{_localstatedir}/run/%{name}
%dir %{_sysconfdir}/%{name}
#%doc %{_mandir}/man8/*
#%doc %{_mandir}/man5/*

%files -n libeap-devel
%defattr(-,root,root,-)
%{_includedir}/eap_peer
%{_libdir}/libeap.so
%{_libdir}/pkgconfig/*.pc

%files -n libeap
%defattr(-,root,root,-)
%{_libdir}/libeap.so.0*

