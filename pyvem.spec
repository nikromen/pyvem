Name:           pyvem
Version:        1.0.0
Release:        %autorelease
Summary:        Manage pipenv, poetry, virtualenv and more virtual envs from one place

License:        GPLv3
URL:            https://github.com/nikromen/%{name}
Source0:        %{url}/archive/refs/tags/%{version}.tar.gz

BuildArch:      noarch

BuildRequires:  python3-devel
BuildRequires:  pyproject-rpm-macros
BuildRequires:  python3-click


%description
%{summary}


%prep
%autosetup


%generate_buildrequires
%pyproject_buildrequires -r


%build
%pyproject_wheel


%install
%pyproject_install
%pyproject_save_files %{name}


%files -n %{name} -f %{pyproject_files}
%license LICENSE
%doc README.md
%{_bindir}/%{name}


%changelog
%autochangelog
