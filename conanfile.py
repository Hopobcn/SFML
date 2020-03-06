from conans import ConanFile, CMake, tools

class SfmlConan(ConanFile):
    name = "sfml"
    version = "2.5.1-head"
    description = 'Simple and Fast Multimedia Library'
    topics = ('conan', 'sfml', 'multimedia')
    homepage = 'https://github.com/SFML/SFML'
    license = "ZLIB"

    export_sources = ["cmake", "extlibs", "include", "src", "test", "tools"]

    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "window": [True, False],
        "graphics": [True, False],
        "network": [True, False],
        "audio": [True, False],
        "enableTests": [True, False]
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "window": True,
        "graphics": True,
        "network": True,
        "audio": True,
        "enableTests": False
    }

    generators = "cmake_find_package", "cmake_paths"

    @property
    def source_subfolder(self):
        return "source_subfolder"

    @property
    def build_subfolder(self):
        return "build_subfolder"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.graphics:
            self.options.window = True

        #self.options["glad"].egl = "1.5"
        #self.options["glad"].gl = "1.1"
        #self.options["glad"].gl_profile = "compatibility"
        #self.options["glad"].glx = "1.4"
        #self.options["glad"].extensions = "GL_ARB_copy_buffer,GL_ARB_fragment_shader,GL_ARB_framebuffer_object,GL_ARB_geometry_shader4,GL_ARB_get_program_binary,GL_ARB_imaging,GL_ARB_multitexture,GL_ARB_separate_shader_objects,GL_ARB_shader_objects,GL_ARB_shading_language_100,GL_ARB_texture_non_power_of_two,GL_ARB_vertex_buffer_object,GL_ARB_vertex_program,GL_ARB_vertex_shader,GL_EXT_blend_equation_separate,GL_EXT_blend_func_separate,GL_EXT_blend_minmax,GL_EXT_blend_subtract,GL_EXT_copy_texture,GL_EXT_framebuffer_blit,GL_EXT_framebuffer_multisample,GL_EXT_framebuffer_object,GL_EXT_geometry_shader4,GL_EXT_packed_depth_stencil,GL_EXT_subtexture,GL_EXT_texture_array,GL_EXT_texture_object,GL_EXT_texture_sRGB,GL_EXT_vertex_array,GL_INGR_blend_func_separate,GL_KHR_debug,GL_NV_geometry_program4,GL_NV_vertex_program,GL_SGIS_texture_edge_clamp,GL_EXT_sRGB,GL_OES_blend_equation_separate,GL_OES_blend_func_separate,GL_OES_blend_subtract,GL_OES_depth24,GL_OES_depth32,GL_OES_framebuffer_object,GL_OES_packed_depth_stencil,GL_OES_single_precision,GL_OES_texture_npot"

    def requirements(self):
        if self.options.graphics:
            self.requires.add("freetype/2.10.1")
            self.requires.add("stb/20200203")
        if self.options.audio:
            self.requires.add("openal/1.19.1")
            self.requires.add("flac/1.3.2@bincrafters/stable")
            self.requires.add("ogg/1.3.4")
            self.requires.add("vorbis/1.3.6")
        if self.options.window:
            self.requires.add("glad/0.2.0")
            self.requires.add("vulkan-headers/1.1.107")
        #    if self.settings.os == "Linux":
        #        self.requires('libx11/1.6.8@bincrafters/stable')
        #        self.requires('libxrandr/1.5.2@bincrafters/stable')
        #        self.requires('mesa/19.3.1@bincrafters/stable')
        if self.options.enableTests:
            self.requires.add("catch2/2.11.0")

    def system_requirements(self):
        if self.settings.os == 'Linux' and tools.os_info.is_linux:
            if tools.os_info.with_apt:
                installer = tools.SystemPackageTool()
                packages = []
                if self.options.window:
                    packages.extend(['libudev-dev'])
                    #packages.extend(['libx11'])
                    #packages.extend(['libxrandr'])
                    #packages.extend(['mesa'])

                for package in packages:
                    installer.installed(package)

    def build_requirements(self):
        if self.settings.os == 'Linux':
            if not tools.which('pkg-config'):
                self.build_requires('pkg-config_installer/0.29.2@bincrafters/stable')

    def _configure_cmake(self):
        cmake = CMake(self)
        #cmake.definitions['SFML_DEPENDENCIES_INSTALL_PREFIX'] = self.package_folder
        #cmake.definitions['SFML_MISC_INSTALL_PREFIX'] = self.package_folder
        cmake.definitions['SFML_BUILD_WINDOW'] = self.options.window
        cmake.definitions['SFML_BUILD_GRAPHICS'] = self.options.graphics
        cmake.definitions['SFML_BUILD_NETWORK'] = self.options.network
        cmake.definitions['SFML_BUILD_AUDIO'] = self.options.audio
        if self.settings.os == "Macos":
            cmake.definitions['SFML_OSX_FRAMEWORK'] = "-framework AudioUnit"
        elif self.settings.compiler == 'Visual Studio':
            if self.settings.compiler.runtime == 'MT' or self.settings.compiler.runtime == 'MTd':
                cmake.definitions['SFML_USE_STATIC_STD_LIBS'] = True

        cmake.configure(build_folder=self.build_subfolder())
        return cmake

    def build(self):
        cmake = self._configure_cmake()
        cmake.build()
        if self.options.enableTests:
            cmake.test()

    def package(self):
        self.copy(pattern='license.md', dst='licenses', src=self._source_subfolder)
        cmake = self._configure_cmake()
        cmake.install()
        if self.settings.os == 'Macos' and self.options.shared and self.options.graphics:
            with tools.chdir(os.path.join(self.package_folder, 'lib')):
                suffix = '-d' if self.settings.build_type == 'Debug' else ''
                graphics_library = 'libsfml-graphics%s.%s.dylib' % (suffix, self.version)
                old_path = '@rpath/../Frameworks/freetype.framework/Versions/A/freetype'
                new_path = '@loader_path/../freetype.framework/Versions/A/freetype'
                command = 'install_name_tool -change %s %s %s' % (old_path, new_path, graphics_library)
                self.output.warn(command)
                self.run(command)

    def package_info(self):
        self.cpp_info.defines = ['SFML_STATIC'] if not self.options.shared else []

        suffix = '-s' if not self.options.shared else ''
        suffix += '-d' if self.settings.build_type == 'Debug' else ''
        sfml_main_suffix = '-d' if self.settings.build_type == 'Debug' else ''

        if self.options.graphics:
            self.cpp_info.libs.append('sfml-graphics' + suffix)
        if self.options.window:
            self.cpp_info.libs.append('sfml-window' + suffix)
        if self.options.network:
            self.cpp_info.libs.append('sfml-network' + suffix)
        if self.options.audio:
            self.cpp_info.libs.append('sfml-audio' + suffix)
        if self.settings.os == 'Windows':
            self.cpp_info.libs.append('sfml-main' + sfml_main_suffix)
        self.cpp_info.libs.append('sfml-system' + suffix)

        if not self.options.shared:
            if self.settings.os == 'Windows':
                if self.options.window:
                    self.cpp_info.libs.append('opengl32')
                    self.cpp_info.libs.append('gdi32')
                if self.options.network:
                    self.cpp_info.libs.append('ws2_32')
                self.cpp_info.libs.append('winmm')
            elif self.settings.os == 'Linux':
                if self.options.graphics:
                    self.cpp_info.libs.append('GL')
                    self.cpp_info.libs.append('udev')
            elif self.settings.os == "Macos":
                frameworks = []
                if self.options.window:
                    frameworks.extend(['Cocoa', 'IOKit', 'Carbon', 'OpenGL'])
                for framework in frameworks:
                    self.cpp_info.exelinkflags.append("-framework %s" % framework)
                self.cpp_info.exelinkflags.append("-ObjC")
                self.cpp_info.sharedlinkflags = self.cpp_info.exelinkflags

