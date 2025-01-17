# Copyright (C) 2015  Codethink Limited
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.


'''Sandbox loader module for App Container images.'''


import contextlib
import json
import os
import shutil
import tarfile
import tempfile


# Mandated by https://github.com/appc/spec/blob/master/SPEC.md#execution-environment
BASE_ENVIRONMENT = {
    'PATH': '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
}


def is_app_container_image(path):
    return path.endswith('.aci')


@contextlib.contextmanager
def unpack_app_container_image(image_file):
    tempdir = tempfile.mkdtemp()
    try:
        # FIXME: you gotta be root, sorry.
        with tarfile.open(image_file, 'r') as tf:
            def is_within_directory(directory, target):
                
                abs_directory = os.path.abspath(directory)
                abs_target = os.path.abspath(target)
            
                prefix = os.path.commonprefix([abs_directory, abs_target])
                
                return prefix == abs_directory
            
            def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
            
                for member in tar.getmembers():
                    member_path = os.path.join(path, member.name)
                    if not is_within_directory(path, member_path):
                        raise Exception("Attempted Path Traversal in Tar File")
            
                tar.extractall(path, members, numeric_owner=numeric_owner) 
                
            
            safe_extract(tf, path=tempdir)

        manifest_path = os.path.join(tempdir, 'manifest')
        rootfs_path = os.path.join(tempdir, 'rootfs')

        with open(manifest_path, 'r') as f:
            manifest_data = json.load(f)

        yield rootfs_path, manifest_data
    finally:
        shutil.rmtree(tempdir)
