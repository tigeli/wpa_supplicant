Name:       wpa_supplicant

Summary:    WPA/WPA2/IEEE 802.1X Supplicant
Version:    2.4
Release:    1
Group:      System Environment/Base
License:    GPLv2
URL:        http://w1.fi/wpa_supplicant/
Source0:    %{name}-%{version}.tar.gz
Source1:    build-config
Source2:    %{name}.conf
Source3:    %{name}.service
Source4:    %{name}.sysconfig
BuildRequires:  pkgconfig(libnl-3.0)
BuildRequires:  pkgconfig(dbus-1)
BuildRequires:  pkgconfig(openssl)
BuildRequires:  readline-devel
# Required for systemctl
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd
# Required for rm
Requires(post): coreutils

%description
wpa_supplicant is a WPA Supplicant for Linux, BSD and Windows with support
for WPA and WPA2 (IEEE 802.11i / RSN). Supplicant is the IEEE 802.1X/WPA
component that is used in the client stations. It implements key negotiation
with a WPA Authenticator and it controls the roaming and IEEE 802.11
authentication/association of the wlan driver.

%prep
%setup -q -n %{name}-%{version}/hostap

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

# man pages
#install -d %{buildroot}%{_mandir}/man{5,8}
#install -m 0644 %{name}/doc/docbook/*.8 %{buildroot}%{_mandir}/man8
#install -m 0644 %{name}/doc/docbook/*.5 %{buildroot}%{_mandir}/man5

# some cleanup in docs and examples
rm -f  %{name}/doc/.cvsignore
rm -rf %{name}/doc/docbook
chmod -R 0644 %{name}/examples/*.py

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
rm /var/log/wpa_supplicant.log || :

%postun
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
# Lets not restart wpa_supplicant on postun to make sure network connectivity is not
# broken during update process.

%files
%defattr(-,root,root,-)
%doc COPYING %{name}/ChangeLog README %{name}/eap_testing.txt %{name}/todo.txt %{name}/wpa_supplicant.conf %{name}/examples
%config(noreplace) %{_sysconfdir}/%{name}/%{name}.conf
%config(noreplace) %{_sysconfdir}/sysconfig/%{name}
/%{_lib}/systemd/system/%{name}.service
%{_sysconfdir}/dbus-1/system.d/%{name}.conf
%{_datadir}/dbus-1/system-services/fi.epitest.hostap.WPASupplicant.service
%{_datadir}/dbus-1/system-services/fi.w1.wpa_supplicant1.service
%{_sbindir}/wpa_passphrase
%{_sbindir}/wpa_supplicant
%{_sbindir}/wpa_cli
%dir %{_sysconfdir}/%{name}
#%doc %{_mandir}/man8/*
#%doc %{_mandir}/man5/*
