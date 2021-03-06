#!/usr/bin/env python3

import sys

__version__ = '0.1'

to_release = ''


# get current version
def get_current_version(name):
    with open('{name}/PKGBUILD'.format(name=name), 'r') as file:
        for line in file:
            if 'pkgver' in line:
                return str(line[7:].strip())  # pkgver=...


# update pkgbuild
def update_pkgbuild(name, url, current_version, available_version):
    global to_release

    os.system("sed 's/pkgrel=.*/pkgrel=1/' -i {name}/PKGBUILD".format(name=name))  # pkgrel=1

    sha512 = str(os.popen('wget -q -O- {url} | sha512sum -'.format(url=url)).read().strip(' -\n'))  # calculate sha512

    os.system(
        "sed 's/{current_version}/{available_version}/' -i {name}/PKGBUILD".format(current_version=current_version,
                                                                                   available_version=available_version,
                                                                                   name=name))  # change version

    url = url.replace('/', '\/').replace(available_version, '$pkgver')

    os.system("sed 's/source=.*/source=("'"{url}"'")/' -i {name}/PKGBUILD".format(url=url, name=name))  # write new url

    os.system("sed 's/sha512sums=.*/sha512sums=('\\''{sha512}'\\'')/' -i {name}/PKGBUILD".format(sha512=sha512,
                                                                                                 name=name))  # write new sha512

    to_release += (name + '\n')

    print('Successfully updated {name} from {current_version} to {available_version}'.format(name=name,
                                                                                             current_version=current_version,
                                                                                             available_version=available_version))


# update python packages version
def python_packages_version_check(name):
    pypi_name = str(name[7:])  # python-...

    if 'python2' in name:
        pypi_name = name[8:]  # python2-...

    req = requests.get('https://pypi.python.org/pypi/{name}/json'.format(name=pypi_name))  # pypi json api ^-^

    if req.ok:
        current_version = get_current_version(name)

        data = json.loads(req.text.encode())

        try:
            available_version = str(max([distutils.version.LooseVersion(release) for release in data['releases'] if
                                         not packaging.version.parse(release).is_prerelease]))  # got new version
            if available_version != current_version:
                url = str(data.get('releases')[available_version][-1]['url'])

                if url[-3:] != 'whl' and url[-3:] != 'egg':
                    update_pkgbuild(name, url, current_version, available_version)
                else:
                    print(
                        'Please, do manual update {name} to {version}, because i cant find any *.tar.gz or *.zip archives'.format(
                            name=name, version=available_version))

        except Exception:
            print('Please, do manual update {name}, because some error occured'.format(name=name))


# update ruby packages version
def ruby_packages_version_check(name):
    ruby_name = name[5:]

    req = requests.get('https://rubygems.org/api/v1/gems/{name}.json'.format(name=ruby_name))  # ruby json api ^-^

    if req.ok:
        current_version = get_current_version(name)

        available_version = str(json.loads(req.text.encode()).get('version'))

        if available_version != current_version:
            url = str(json.loads(req.text.encode()).get('gem_uri'))
            update_pkgbuild(name, url, current_version, available_version)


def main(function, needed):
    to_check = []

    exclusion = ['python2-cement', 'python2-nmap', 'python2-pubsub', 'python2-pynfc', 'python2-slugify', 'ruby-unf']

    for root, dirs, files in os.walk('.'):
        for dir in dirs:
            if needed in dir and dir not in exclusion:
                to_check.append(dir)

    with ThreadPoolExecutor(16) as executor:  # i think 16 is enough
        for _ in executor.map(function, to_check):
            pass


if __name__ == '__main__':
    try:
        import distutils.version, json, os, packaging.version, requests
        from concurrent.futures import ThreadPoolExecutor
    except ModuleNotFoundError as e:
        print('Failure importing module: ' + str(e))
        sys.exit(1)

    main(python_packages_version_check, 'python')  # start version updating python packages

    main(ruby_packages_version_check, 'ruby')  # start version updating ruby packages

    with open('../lists/to-release', 'a') as file:
        file.write(to_release)

    print('Done!')

