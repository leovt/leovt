'''
Author: leovt (Leonhard Vogt)
License: GNU GENERAL PUBLIC LICENSE - Version 3, 29 June 2007

Example code for using glsl and vertex buffer objects with pyglet
'''

import pyglet
from pyglet import gl
import ctypes

vertexbuffer = gl.GLuint(0)

def shader(shader_type, shader_source):
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


def setup_program():
    '''
    Create the glsl program
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

    program = gl.glCreateProgram()
    gl.glAttachShader(program, shader(gl.GL_VERTEX_SHADER, vertex_shader))
    gl.glAttachShader(program, shader(gl.GL_FRAGMENT_SHADER, fragment_shader))
    gl.glLinkProgram(program)
    gl.glUseProgram(program)
    return program


class VERTEX(ctypes.Structure):
    _fields_ = [
        ('position', gl.GLfloat * 2),
        ('color', gl.GLfloat * 4),
    ]


def setup_vertexbuffer(program):
    '''
    Create the vertexbuffer object
    '''
    gl.glGenBuffers(1, ctypes.byref(vertexbuffer))
    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vertexbuffer)

    loc_position = gl.glGetAttribLocation(program, ctypes.create_string_buffer(b'position'))
    loc_color = gl.glGetAttribLocation(program, ctypes.create_string_buffer(b'color'))

    if loc_position < 0:
        print('Warning: position is not used in the shader')
    if loc_color < 0:
        print('Warning: color is not used in the shader')

    gl.glEnableVertexAttribArray(loc_position)
    gl.glVertexAttribPointer(loc_position, 2, gl.GL_FLOAT, False, ctypes.sizeof(VERTEX), ctypes.c_void_p(VERTEX.position.offset))

    gl.glEnableVertexAttribArray(loc_color)
    gl.glVertexAttribPointer(loc_color, 4, gl.GL_FLOAT, False, ctypes.sizeof(VERTEX), ctypes.c_void_p(VERTEX.color.offset))


def draw():
    data = (VERTEX * 3)(((-0.6, -0.5), (1.0, 0.0, 0.0, 1.0)),
                      ((0.6, -0.5), (0.0, 1.0, 0.0, 1.0)),
                      ((0.0, 0.5), (0.0, 0.0, 1.0, 1.0)))

    gl.glClearColor(0.5, 0.6, 0.7, 1.0)
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vertexbuffer)
    gl.glBufferData(gl.GL_ARRAY_BUFFER, ctypes.sizeof(data), data, gl.GL_DYNAMIC_DRAW)
    gl.glDrawArrays(gl.GL_TRIANGLES, 0, 3)


def main():
    window = pyglet.window.Window()
    program = setup_program()
    setup_vertexbuffer(program)
    print('OpenGL Version {}'.format(window.context.get_info().get_version()))
    window.on_draw = draw
    pyglet.clock.schedule_interval(lambda dt:None, 0.01)
    pyglet.app.run()


if __name__ == '__main__':
    main()
