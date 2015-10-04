'''
Author: leovt (Leonhard Vogt)
License: GNU GENERAL PUBLIC LICENSE - Version 3, 29 June 2007

Example code for using glsl and vertex buffer objects with pyglet
'''

import pyglet
from pyglet import gl
import ctypes

render_vertexbuffer = gl.GLuint(0)
render_vao = gl.GLuint(0)
render_program = 0

copy_vertexbuffer = gl.GLuint(0)
copy_vao = gl.GLuint(0)
copy_program = 0

framebuffer = gl.GLuint(0)
rendered_texture = gl.GLuint(0)


FB_WIDTH = 30
FB_HEIGHT = 20

def compile_shader(shader_type, shader_source):
    '''
    Compile a shader and print error messages.
    '''
    shader_name = gl.glCreateShader(shader_type)
    src_buffer = ctypes.create_string_buffer(shader_source)
    buf_pointer = ctypes.cast(ctypes.pointer(ctypes.pointer(src_buffer)), ctypes.POINTER(ctypes.POINTER(ctypes.c_char)))
    length = ctypes.c_int(len(shader_source) + 1)
    gl.glShaderSource(shader_name, 1, buf_pointer, ctypes.byref(length))
    gl.glCompileShader(shader_name)

    # test if compilation is succesful and print status messages
    success = gl.GLint(0)
    gl.glGetShaderiv(shader_name, gl.GL_COMPILE_STATUS, ctypes.byref(success))

    length = gl.GLint(0)
    gl.glGetShaderiv(shader_name, gl.GL_INFO_LOG_LENGTH, ctypes.byref(length))
    log_buffer = ctypes.create_string_buffer(length.value)
    gl.glGetShaderInfoLog(shader_name, length, None, log_buffer)

    for line in log_buffer.value[:length.value].decode('ascii').splitlines():
        print('GLSL: ' + line)

    assert success, 'Compiling of the shader failed.'

    return shader_name


def link_program(program):
    ''' link a glsl program and print error messages.'''
    gl.glLinkProgram(program)

    length = gl.GLint(0)
    gl.glGetProgramiv(program, gl.GL_INFO_LOG_LENGTH, ctypes.byref(length))
    log_buffer = ctypes.create_string_buffer(length.value)
    gl.glGetProgramInfoLog(program, length, None, log_buffer)

    for line in log_buffer.value[:length.value].decode('ascii').splitlines():
        print('GLSL: ' + line)


def setup_render_program():
    '''
    Create the glsl program for rendering the colored triangle
    '''
    vertex_shader = b'''
        attribute vec2 position;
        attribute vec4 color;
        
        varying vec4 var_color;

        void main()
        {
            gl_Position = vec4(position, 0.0, 1.0);
            var_color = color;
        }
    '''

    fragment_shader = b'''
        varying vec4 var_color;
        void main()
        {
            gl_FragColor = var_color;
        }
    '''

    global render_program
    render_program = gl.glCreateProgram()
    gl.glAttachShader(render_program, compile_shader(gl.GL_VERTEX_SHADER, vertex_shader))
    gl.glAttachShader(render_program, compile_shader(gl.GL_FRAGMENT_SHADER, fragment_shader))
    link_program(render_program)


def setup_copy_program():
    '''
    Create the glsl copy_program for copying the rendered texture
    '''
    vertex_shader = b'''
        attribute vec2 position;
        attribute vec2 texcoord;
        
        varying vec2 var_texcoord;

        void main()
        {
            gl_Position = vec4(position, 0.0, 1.0);
            var_texcoord = texcoord;
        }
    '''

    fragment_shader = b'''
        uniform sampler2D texture;
        varying vec2 var_texcoord;
        
        void main()
        {
            gl_FragColor = texture2D(texture, var_texcoord);
        }
    '''

    global copy_program
    copy_program = gl.glCreateProgram()
    gl.glAttachShader(copy_program, compile_shader(gl.GL_VERTEX_SHADER, vertex_shader))
    gl.glAttachShader(copy_program, compile_shader(gl.GL_FRAGMENT_SHADER, fragment_shader))
    link_program(copy_program)


class COLOR_VERTEX(ctypes.Structure):
    _fields_ = [
        ('position', gl.GLfloat * 2),
        ('color', gl.GLfloat * 4),
    ]

class TEXTURE_VERTEX(ctypes.Structure):
    _fields_ = [
        ('position', gl.GLfloat * 2),
        ('texcoord', gl.GLfloat * 2),
    ]


def setup_render_vertexbuffer():
    '''
    Create the vertexbuffer object for the rendering program
    '''
    gl.glGenVertexArrays(1, ctypes.byref(render_vao))
    gl.glGenBuffers(1, ctypes.byref(render_vertexbuffer))

    loc_position = gl.glGetAttribLocation(render_program, ctypes.create_string_buffer(b'position'))
    loc_color = gl.glGetAttribLocation(render_program, ctypes.create_string_buffer(b'color'))

    if loc_position < 0:
        print('Warning: position is not used in the shader')
    if loc_color < 0:
        print('Warning: color is not used in the shader')


    gl.glBindVertexArray(render_vao)

    gl.glEnableVertexAttribArray(loc_position)
    gl.glEnableVertexAttribArray(loc_color)

    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, render_vertexbuffer)

    gl.glVertexAttribPointer(loc_position, 2, gl.GL_FLOAT, False, ctypes.sizeof(COLOR_VERTEX), ctypes.c_void_p(COLOR_VERTEX.position.offset))
    gl.glVertexAttribPointer(loc_color, 4, gl.GL_FLOAT, False, ctypes.sizeof(COLOR_VERTEX), ctypes.c_void_p(COLOR_VERTEX.color.offset))

    gl.glBindVertexArray(0)

def setup_copy_vertexbuffer():
    '''
    Create the vertexbuffer object for the copying program
    '''
    # gl.glGenVertexArrays(1, ctypes.byref(copy_vao))
    gl.glGenBuffers(1, ctypes.byref(copy_vertexbuffer))

    loc_position = gl.glGetAttribLocation(copy_program, ctypes.create_string_buffer(b'position'))
    loc_texcoord = gl.glGetAttribLocation(copy_program, ctypes.create_string_buffer(b'texcoord'))

    if loc_position < 0:
        print('Warning: position is not used in the shader')
    if loc_texcoord < 0:
        print('Warning: texcoord is not used in the shader')

    gl.glBindVertexArray(copy_vao)

    gl.glEnableVertexAttribArray(loc_position)
    gl.glEnableVertexAttribArray(loc_texcoord)

    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, copy_vertexbuffer)

    gl.glVertexAttribPointer(loc_position, 2, gl.GL_FLOAT, False, ctypes.sizeof(TEXTURE_VERTEX), ctypes.c_void_p(TEXTURE_VERTEX.position.offset))
    gl.glVertexAttribPointer(loc_texcoord, 2, gl.GL_FLOAT, False, ctypes.sizeof(TEXTURE_VERTEX), ctypes.c_void_p(TEXTURE_VERTEX.texcoord.offset))

    gl.glBindVertexArray(0)


def draw():
    render_to_texture()
    copy_texture_to_screen()


def render_to_texture():
    # select the target to draw into
    gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, framebuffer)
    draw_buffers = (gl.GLenum * 1)(gl.GL_COLOR_ATTACHMENT0)
    gl.glDrawBuffers(1, draw_buffers)
    gl.glViewport(0, 0, FB_WIDTH, FB_HEIGHT)

    # clear the destination
    gl.glClearColor(0.5, 0.6, 0.7, 1.0)
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

    # prepare the rendering
    gl.glUseProgram(render_program)

    # send the vertex data
    data = (COLOR_VERTEX * 3)(((-0.6, -0.5), (1.0, 0.0, 0.0, 1.0)),
                      ((0.6, -0.5), (0.0, 1.0, 0.0, 1.0)),
                      ((0.0, 0.5), (0.0, 0.0, 1.0, 1.0)))

    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, render_vertexbuffer)
    gl.glBufferData(gl.GL_ARRAY_BUFFER, ctypes.sizeof(data), data, gl.GL_DYNAMIC_DRAW)

    # draw using the vertex array for vertex information
    gl.glBindVertexArray(render_vao)
    gl.glDrawArrays(gl.GL_TRIANGLES, 0, 3)
    gl.glBindVertexArray(0)


def copy_texture_to_screen():
    # select the target to draw into
    gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
    gl.glViewport(0, 0, window.width, window.height)

    # clear the destination
    gl.glClearColor(0.4, 0.4, 0.4, 1.0)
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

    # select the program for drawing
    gl.glUseProgram(copy_program)

    # send the vertex data
    data = (TEXTURE_VERTEX * 8)(((-0.9, -0.9), (0.0, 0.0)),
                                ((0.5, -0.9), (1.0, 0.0)),
                                ((0.5, 0.5), (1.0, 1.0)),
                                ((-0.9, 0.5), (0.0, 1.0)),

                                ((0.6, 0.6), (0.0, 1.0)),
                                ((1.0, 0.6), (1.0, 1.0)),
                                ((1.0, 1.0), (1.0, 0.0)),
                                ((0.6, 1.0), (0.0, 0.0)),
                                )

    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, copy_vertexbuffer)
    gl.glBufferData(gl.GL_ARRAY_BUFFER, ctypes.sizeof(data), data, gl.GL_DYNAMIC_DRAW)


    # draw
    gl.glBindVertexArray(copy_vao)
    gl.glDrawArrays(gl.GL_QUADS, 0, 8)
    gl.glBindVertexArray(0)


def setup_framebuffer():
    gl.glGenFramebuffers(1, ctypes.byref(framebuffer))
    gl.glGenTextures(1, ctypes.byref(rendered_texture))

    gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, framebuffer)

    # Set up the texture as the target for color output
    gl.glBindTexture(gl.GL_TEXTURE_2D, rendered_texture)
    gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGB, FB_WIDTH, FB_HEIGHT, 0, gl.GL_RGB, gl.GL_UNSIGNED_BYTE, 0)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
    gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, rendered_texture, 0)

    draw_buffers = (gl.GLenum * 1)(gl.GL_COLOR_ATTACHMENT0)
    gl.glDrawBuffers(1, draw_buffers)

    assert gl.glCheckFramebufferStatus(gl.GL_FRAMEBUFFER) == gl.GL_FRAMEBUFFER_COMPLETE


def main():
    global window
    window = pyglet.window.Window()

    setup_framebuffer()
    setup_render_program()
    setup_render_vertexbuffer()
    setup_copy_program()
    setup_copy_vertexbuffer()

    print('OpenGL Version {}'.format(window.context.get_info().get_version()))
    window.on_draw = draw
    pyglet.clock.schedule_interval(lambda dt:None, 0.01)
    pyglet.app.run()


if __name__ == '__main__':
    main()
