from OpenGL.GL import *

def compile_shader(source, shader_type):
    shader = glCreateShader(shader_type)
    glShaderSource(shader, source)
    glCompileShader(shader)

    # Check compile errors
    if glGetShaderiv(shader, GL_COMPILE_STATUS) != GL_TRUE:
        info = glGetShaderInfoLog(shader).decode()
        raise RuntimeError(f"Shader compile failed: {info}")
    return shader

def create_program(vertex_src, fragment_src):
    vert = compile_shader(vertex_src, GL_VERTEX_SHADER)
    frag = compile_shader(fragment_src, GL_FRAGMENT_SHADER)
    program = glCreateProgram()
    glAttachShader(program, vert)
    glAttachShader(program, frag)
    glLinkProgram(program)

    if glGetProgramiv(program, GL_LINK_STATUS) != GL_TRUE:
        info = glGetProgramInfoLog(program).decode()
        raise RuntimeError(f"Program link failed: {info}")

    glDeleteShader(vert)
    glDeleteShader(frag)
    return program
