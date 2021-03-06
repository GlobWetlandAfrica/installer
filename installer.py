import os
import sys
import glob
import errno
import shutil
import functools
import subprocess
import traceback
import tempfile
import datetime
import logging
from zipfile import ZipFile
from distutils import dir_util

from PyQt5 import QtCore, QtWidgets
from installerGUI import installerWelcomeWindow
from installerGUI import GenericInstallWindow, DirPathPostInstallWindow
from installerGUI import extractingWaitWindow, copyingWaitWindow
from installerGUI import cmdWaitWindow
from installerGUI import uninstallInstructionsWindow
from installerGUI import finishWindow
from installerGUI import CANCEL, SKIP, NEXT

import installer_utils

logger = logging.getLogger('gwa_installer')


def _set_logfile_handler():
    datestr = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    logfile = os.path.join(tempfile.gettempdir(), 'gwa_install_{}.log'.format(datestr))
    logger.setLevel('DEBUG')
    fh = logging.FileHandler(logfile)
    fh.setLevel('DEBUG')
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logfile


class Installer():

    def __init__(self, logfile):
        self.util = Utilities(logfile)

    def runInstaller(self):
        ########################################################################
        # welcome window with license
        self.dialog = installerWelcomeWindow()
        res = self.showDialog()

        if res == NEXT:

            # select default installation directories for 64 bit install
            install_dirs = {'OSGeo4W': "C:\\OSGeo4W64",
                            'SNAP': "C:\\Program Files\\SNAP",
                            'R': "C:\\Program Files\\R\\R-4.0.2"}

            # select installation files for 64 bit install
            installationsDir = 'Installations_x64'
            _joinbindir = functools.partial(os.path.join, installationsDir)
            osgeo4wInstall = _joinbindir("osgeo4w-setup.bat")
            snapInstall = [_joinbindir('esa-snap_sentinel_windows-x64_7_0.exe'), '-q',
                           '-varfile', 'SNAP_response_install4j.varfile',
                           '-splash', '"SNAP installation"']
            rInstall = _joinbindir("R-4.0.2-win.exe")

        elif res == CANCEL:
            del self.dialog
            return
        else:
            self.unknownActionPopup()

        ########################################################################
        # Information about uninstalling old version
        self.dialog = uninstallInstructionsWindow()
        res = self.showDialog()
        if res == CANCEL:
            del self.dialog
            return

        ########################################################################
        # Install OSGeo4W (QGIS, SAGA, GRASS)

        # Define RAM fraction to use (SNAP and BEAM)
        ram_fraction = 0.6

        self.dialog = GenericInstallWindow('OSGeo4W')
        res = self.showDialog()

        # run the OSGeo4W installation here as an outside process
        if res == NEXT:
            self.util.execSubprocess(osgeo4wInstall)
        elif res == SKIP:
            pass
        elif res == CANCEL:
            del self.dialog
            return
        else:
            self.unknownActionPopup()

        # ask for post-installation even if user has skipped installation
        self.dialog = DirPathPostInstallWindow('OSGeo4W', install_dirs['OSGeo4W'])
        res = self.showDialog()

        # copy plugins, scripts, and models and activate processing providers
        if res == NEXT:
            install_dirs['OSGeo4W'] = str(self.dialog.dirPathText.toPlainText())
            qgis_profile_path = os.path.join(os.path.expanduser("~"), "AppData", "Roaming", "QGIS"
                                             "QGIS3", "profiles", "default")

            QGIS_extras_dir = os.path.abspath("QGIS additional software")
            # copy the plugins
            dstPath = os.path.join(qgis_profile_path, "python", "plugins")
            srcPath = os.path.join(QGIS_extras_dir, "plugins", "plugins.zip")
            # try to delete old plugins before copying the new ones to avoid conflicts
            plugins_to_delete = [
                'mikecprovider',
                'processing',
                'processing_gpf',
                'photo2shape',
                'processing_workflow',
                'openlayers_plugin',
                'pointsamplingtool',
                'temporalprofiletool',
                'valuetool']
            for plugin in plugins_to_delete:
                self.util.deleteDir(
                    os.path.join(dstPath, plugin))
            self.dialog = extractingWaitWindow(self.util, srcPath, dstPath)
            self.showDialog()

            # copy scripts and models
            processing_dir = os.path.join(qgis_profile_path, "processing")
            processing_packages = glob.glob(os.path.join(QGIS_extras_dir, '*.zip'))
            logger.info('Found processing packages: %s', processing_packages)
            for zipfname in processing_packages:
                # show dialog because it might take some time on slower computers
                self.dialog = extractingWaitWindow(self.util, zipfname, processing_dir)
                self.showDialog()

            # copy additional python packages
            site_packages_dir = os.path.join(
                install_dirs['OSGeo4W'], 'apps', 'Python37', 'Lib', 'site-packages')
            python_packages = glob.glob(os.path.join(QGIS_extras_dir, 'python_packages', '*.zip'))
            logger.info('Found python packages: %s', python_packages)
            for zipfname in python_packages:
                self.dialog = extractingWaitWindow(self.util, zipfname, site_packages_dir)
                self.showDialog()

            # install additional python packages with pip
            pip_package_dir = os.path.join(QGIS_extras_dir, 'python_packages_pip')
            cmd, cmdkw = self.util.cmd_install_pip_offline(
                osgeo_root=install_dirs['OSGeo4W'],
                package_dir=pip_package_dir)
            self.dialog = cmdWaitWindow(self.util, cmd, **cmdkw)
            self.showDialog()

            # activate plugins and processing providers
            self.util.activatePlugins()
            self.util.activateProcessingProviders(install_dirs['OSGeo4W'])
        elif res == SKIP:
            pass
        elif res == CANCEL:
            del self.dialog
            return
        else:
            self.unknownActionPopup()


        ########################################################################
        # Install Snap Toolbox

        self.dialog = GenericInstallWindow('SNAP')
        res = self.showDialog()

        # run the Snap installation here as an outside process
        if res == NEXT:
            self.util.execSubprocess(snapInstall)

            # Configure snappy
            site_packages_dir = os.path.join(
                install_dirs['OSGeo4W'], 'apps', 'Python37', 'Lib', 'site-packages')
            osgeopython = os.path.join(install_dirs['OSGeo4W'], 'bin', 'python-qgis-ltr.bat')
            self.util.execSubprocess([os.path.join(install_dirs['SNAP'], "bin", "snap64.exe"),
                                     "--nogui", "--python", osgeopython, site_packages_dir])

            jpyconfig = os.path.join(site_packages_dir, 'jpyconfig.py')
            replace = {
                'java_home': '"{}"'.format(os.path.join(install_dirs['SNAP'], 'jre')),
                'jvm_dll': 'None'}
            installer_utils.fix_jpyconfig(jpyconfig, replace=replace)

            # Copy jpy files into snappy directory, otherwise snappy does not work. This is just
            # a quick fix.
            for name in [
                    'jpy.pyd', 'jpy-*.jar', 'jpyconfig.properties', 'jpyconfig.py', 'jpyutil.py',
            ]:
                paths = glob.glob(os.path.join(site_packages_dir, name))
                if not paths:
                    logger.warn('No files found for JPY file pattern "{}".'.format(name))
                for path in paths:
                    shutil.copy(path, os.path.join(site_packages_dir, 'snappy'))

            # Set ammount of memory to be used with SNAP
            java_max_mem = installer_utils.get_total_ram() * ram_fraction
            logger.info('Java max mem: {}'.format(java_max_mem))
            snappy_ini = os.path.join(site_packages_dir, 'snappy', 'snappy.ini')
            try:
                with open(snappy_ini, 'w') as f:
                    f.write(
                        '[DEFAULT]\n'
                        'snap_home={}\n'
                        'java_max_mem={:.0f}m\n'
                        .format(install_dirs['SNAP'], java_max_mem))
            except IOError:
                logger.warn('Could not find snappy.ini to set max memory')
            settingsfile = os.path.join(install_dirs['SNAP'], 'bin', 'gpt.vmoptions')
            try:
                installer_utils.modifyRamInBatFiles(settingsfile, ram_fraction)
            except IOError as exc:
                self.util.error_exit(str(exc))

            # Enable per-pixel-geocoding for OLCI and MERIS
            try:
                with open(os.path.join(os.path.expanduser("~"), ".snap", "etc", "s3tbx.properties"),
                          "a") as fp:
                    fp.write("s3tbx.reader.olci.pixelGeoCoding=true\n")
                    fp.write("s3tbx.reader.meris.pixelGeoCoding=true\n")
            except IOError:
                logger.warn('Could not set options in s3tbx.properties.')

            # Update SNAP modules offline
            dstPath = install_dirs['SNAP']
            srcPath = "SNAP additional modules"
            self.dialog = copyingWaitWindow(self.util, srcPath, dstPath)
            self.showDialog()
            snapUpdate = [os.path.join(install_dirs['SNAP'], "bin", "snap64.exe"),
                          "--nogui", "--modules", "--update-all"]
            self.util.execSubprocess(snapUpdate)

            # Activate QGIS SNAP plugin
            self.util.activateSNAPplugin(install_dirs['SNAP'])

        elif res == SKIP:
            pass
        elif res == CANCEL:
            del self.dialog
            return
        else:
            self.unknownActionPopup()

        # #######################################################################
        # Install R

        self.dialog = GenericInstallWindow('R')
        res = self.showDialog()

        # run the R installation here as an outside process
        if res == NEXT:
            self.util.execSubprocess(rInstall)
            # self.dialog = rPostInstallWindow(install_dirs['R'])
            # res = self.showDialog()
        elif res == SKIP:
            pass
        elif res == CANCEL:
            del self.dialog
            return
        else:
            self.unknownActionPopup()

        # ask for post-installation even if user has skipped installation
        self.dialog = DirPathPostInstallWindow('R', install_dirs['R'])
        res = self.showDialog()

        # Copy the R additional libraries
        if res == NEXT:
            install_dirs['R'] = str(self.dialog.dirPathText.toPlainText())
            self.util.activateRplugin(install_dirs['R'], "true")
        elif res == SKIP:
            pass
        elif res == CANCEL:
            del self.dialog
            return
        else:
            self.unknownActionPopup()


##########################################
# helper functions

class Utilities(QtCore.QObject):
    finished = QtCore.pyqtSignal()

    def __init__(self, logfile):

        QtCore.QObject.__init__(self)
        # QGIS and processing settings
        self.qsettings = QtCore.QSettings("QGIS", "QGIS2")
        # logging
        self.logfile = logfile

    def _log_traceback(self, notify=False, fail=False):
        logger.exception('Something went wrong.')
        if fail:
            raise
        elif notify:
            trace = traceback.format_exc()
            msgBox = QtWidgets.QMessageBox()
            msgBox.setText(
                "An error occurred: {}. Log written to \'{}\'."
                .format(trace, self.logfile))
            msgBox.exec_()

    def execSubprocess(self, command):
        logger.info('Running binary installer: %s', command)
        # First part of a command should be a path to an exe file so check if it exists
        if type(command) is list:
            c = command[0]
        else:
            c = command
        if not os.path.isfile(c):
            msgBox = QtWidgets.QMessageBox()
            msgBox.setText(
                "Could not find the installation file for this component!\n\n "
                "Skipping to next component")
            msgBox.exec_()
            # self.dialog.action = SKIP
            return

        proc = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stdin=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True).stdout
        for line in iter(proc.readline, ""):
            pass

    def execute_cmd(self, cmd, shell=False, notify=False):
        """Execute cmd and save output to log file"""
        logger.info('Executing command: %s', cmd)
        try:
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            output = subprocess.check_output(
                cmd,
                stdin=subprocess.PIPE,
                stderr=subprocess.PIPE,
                startupinfo=si,
                shell=shell)
            logger.info(output)
        except subprocess.CalledProcessError:
            self._log_traceback(notify=notify)
        finally:
            self.finished.emit()

    def cmd_install_pip_offline(self, osgeo_root, package_dir):
        requirements_file = os.path.join(package_dir, 'requirements.txt')
        logger.info('Installing with pip install -r %s', requirements_file)
        if not os.path.isfile(requirements_file):
            self.error_exit('No requirements file found in {}'.format(requirements_file))
        osgeo_envbat = os.path.join(osgeo_root, 'bin', 'o4w_env.bat')
        if not os.path.isfile(osgeo_envbat):
            raise self.error_exit('No OSGeo env bat file found in {}'.format(osgeo_envbat))
        cmd = (
            'call {osgeo_envbat} & '
            'if defined OSGEO4W_ROOT '
            '('
            'python -m pip install --no-index --find-links "{package_dir}" '
            '-r "{requirements_file}"'
            ')'
            .format(
                osgeo_envbat=osgeo_envbat,
                package_dir=package_dir,
                requirements_file=requirements_file))
        kwargs = dict(shell=True, notify=True)
        return cmd, kwargs

    def deleteFile(self, filePath):
        logger.info('Deleting file %s', filePath)
        try:
            os.remove(filePath)
        except OSError:
            self._log_traceback(notify=False)

    def deleteDir(self, dirPath):
        logger.info('Deleting dir %s', dirPath)
        try:
            shutil.rmtree(dirPath, ignore_errors=True)
        except OSError:
            self._log_traceback(notify=False)

    def error_exit(self, msg):
        logger.error(msg)
        msgBox = QtWidgets.QMessageBox()
        msgBox.setText(msg)
        msgBox.exec_()
        self.finished.emit()

    def copyFiles(self, srcPath, dstPath, checkDstParentExists=True):
        logger.info('Copying files from %s to %s', srcPath, dstPath)

        # a simple check to see if we are copying to the right directory by making sure that
        # its parent exists
        if checkDstParentExists:
            if not os.path.isdir(os.path.dirname(dstPath)):
                self.error_exit(
                    "Could not find the destination directory!\n\n "
                    "No files were copied.")
                return

        # checkWritePremissions alsoe creates the directory if it doesn't exist yet
        if not self.checkWritePermissions(dstPath):
            self.error_exit(
                "You do not have permissions to write to destination directory!\n\n "
                "No files were copied.\n\n"
                "Re-run the installer with administrator privileges or manually "
                "copy files from {} to {} to  after the installation process is over."
                .format(srcPath, dstPath))
            return

        # for directories copy the whole directory recursively
        if os.path.isdir(srcPath):
            dir_util.copy_tree(srcPath, dstPath)
        # for files create destination directory is necessary and copy the file
        elif os.path.isfile(srcPath):
            shutil.copy(srcPath, dstPath)
        else:
            msg = "Cannot find the source directory!\n\n No files were copied."
            logger.error(msg)
            msgBox = QtWidgets.QMessageBox()
            msgBox.setText(msg)
            msgBox.exec_()

        self.finished.emit()

    def unzipArchive(self, archivePath, dstPath):
        logger.info('Unzipping %s to %s', archivePath, dstPath)
        if not os.path.isfile(archivePath):
            self.error_exit("Could not find the archive!\n\n No files were extracted.")
            return

        # checkWritePremissions also creates the directory if it doesn't exist yet
        if not self.checkWritePermissions(dstPath):
            self.error_exit(
                "You do not have permissions to write to destination directory!\n\n "
                "No files were copied.\n\n" +
                "Re-run the installer with administrator privileges or manually unzip "
                "files from {} to {} to after the installation process is over."
                .format(archivePath, dstPath))
            return

        with ZipFile(archivePath) as archive:
            archive.extractall(dstPath)
        self.finished.emit()

    def checkWritePermissions(self, dstPath):
        logger.debug('Checking write permissions on %s', dstPath)
        testfile = os.path.join(dstPath, "_test")
        try:
            if not os.path.isdir(dstPath):
                logger.debug('Creating directory in %s', dstPath)
                os.makedirs(dstPath)
            with open(testfile, 'w'):
                pass
        except IOError as e:
            logger.debug('%s', e)
            if e.errno == errno.EACCES:
                return False
            else:
                return False
        else:
            try:
                os.remove(testfile)
            except:
                pass
        return True

    def setQGISSettings(self, name, value):
        logger.info('Set %s to %s', name, value)
        self.qsettings.setValue(name, value)

    def activateThis(self, *names):
        # sets the requested option(s) to 'true'
        for name in names:
            self.setQGISSettings(name, 'true')

    def activatePlugins(self):
        self.activateThis(
            "PythonPlugins/processing_workflow",
            "PythonPlugins/openlayers_plugin",
            "PythonPlugins/photo2shape",
            "PythonPlugins/pointsamplingtool",
            "PythonPlugins/processing",
            "PythonPlugins/temporalprofiletool",
            "PythonPlugins/valuetool",
            "plugins/zonalstatisticsplugin")

    def activateProcessingProviders(self, osgeodir):
        self.setQGISSettings("Processing/configuration/ACTIVATE_GRASS70", "true")
        self.activateThis(
            "Processing/configuration/ACTIVATE_MODEL",
            "Processing/configuration/ACTIVATE_OTB",
            "Processing/configuration/ACTIVATE_QGIS",
            "Processing/configuration/ACTIVATE_SAGA",
            "Processing/configuration/ACTIVATE_DHIGRAS",
            "Processing/configuration/ACTIVATE_SCRIPT",
            "Processing/configuration/ACTIVATE_WORKFLOW",
            "Processing/configuration/ACTIVATE_GWA_TBX",
            "Processing/configuration/GRASS7_LOG_COMMANDS",
            "Processing/configuration/GRASS7_LOG_CONSOLE",
            "Processing/configuration/SAGA_LOG_COMMANDS",
            "Processing/configuration/SAGA_LOG_CONSOLE",
            "Processing/configuration/USE_FILENAME_AS_LAYER_NAME",
            "Processing/configuration/TASKBAR_BUTTON_GWA_TBX")
        self.setQGISSettings("Processing/configuration/TASKBAR_BUTTON_WORKFLOW", "false")
        # GRASS_FOLDER depends on GRASS version and must be set explicitly here
        try:
            grass_root = os.path.join(osgeodir, 'apps', 'grass')
            grass_folders = sorted([
                d for d in glob.glob(os.path.join(grass_root, 'grass-*'))
                if os.path.isdir(d)])
            grassFolder = grass_folders[-1]
            self.setQGISSettings("Processing/configuration/GRASS7_FOLDER", grassFolder)
            self.setQGISSettings("Processing/configuration/GRASS7_HELP_PATH",
                                 os.path.join(grassFolder, "docs", "html"))
        except (IndexError, OSError):
            pass

    def activateSNAPplugin(self, dirPath):
        self.activateThis(
            "PythonPlugins/processing_gpf",
            "Processing/configuration/ACTIVATE_SNAP")
        self.activateThis(
            "Processing/configuration/S1TBX_ACTIVATE",
            "Processing/configuration/S2TBX_ACTIVATE")
        self.setQGISSettings("Processing/configuration/SNAP_FOLDER", dirPath)

    def activateRplugin(self, dirPath, use64):
        self.activateThis(
            "Processing/configuration/ACTIVATE_R")
        self.setQGISSettings("Processing/configuration/R_FOLDER", dirPath)
        self.setQGISSettings("Processing/configuration/R_USE64", use64)


if __name__ == '__main__':

    logfile = _set_logfile_handler()

    try:
        app = QtWidgets.QApplication(sys.argv)

        installer = Installer(logfile=logfile)

        # Fix to make sure that runInstaller is executed in the app event loop
        def _slot_installer():
            QtCore.SLOT(installer.runInstaller())

        QtCore.QTimer.singleShot(200, _slot_installer)

        app.exec_()
    except:
        logger.exception()
        raise
