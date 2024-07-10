OK = 200
SOBRAN_CARACTERES_100 = 452
SOBRAN_CARACTERES_255 = 453
SOBRAN_CARACTERES_10 = 454
SOBRAN_CARACTERES_2 = 455
SOBRAN_CARACTERES_20 = 456
SOBRAN_CARACTERES_1 = 457
SOBRAN_CARACTERES_120 = 458
SOBRAN_CARACTERES_30 = 459
SOBRAN_CARACTERES_50 = 475
FALTAN_CARACTERES = 460
EMAIL_INCORRECTO = 461
EMAIL_NO_EXISTE = 462
TELEFONO_INCORRECTO = 463
KEY_NO_EXISTE = 464
CARACTER_INVALIDO = 465
COUNTRY_NO_EXISTE = 466
TIMEZONE_NO_EXISTE = 467
IDNUMBER_INCORRECTO = 468
USERNAME_INCORRECTO = 469
LANG_NO_EXISTE = 470
NO_ENCONTRADO = 471
CARACTER_INVALIDO_USERNAME = 472
CARACTER_INVALIDO_EMAIL = 473
CARACTER_INVALIDO_ID = 474
QUIZ_NO_EXISTE = 476
COURSE_NO_EXISTE = 477
USER_NO_EXISTE = 478
GROUP_NO_EXISTE = 479
USUARIO_AÑADIDO = 480
GRUPO_AÑADIDO = 481
GRUPO_YA_EXISTE = 482
ASSIGNMENT_NO_EXISTE = 483
NO_MATRICULA_MANUAL = 484
NO_INFORMACION = 485
ACTION_NO_EXISTE = 486
USUARIO_NO_MATRICULADO = 487
DATOS_INVALIDOS = 488
CAMBIO_CONTRASEÑA = 489
ERROR_LOG = 490
NO_BADGES = 491
EVENTO_NO_EXISTE = 492
SIN_PERMISOS = 493
CONTEXT_NO_EXISTE = 494
TOUR_NO_EXISTE = 495
URL_NO_LOCAL = 496
IDNUMBER_VALOR_CAT_MAL = 497


HTTP_MESSAGES = {
    OK: "La operación se realizó correctamente.",
    SOBRAN_CARACTERES_100: "La cantidad de caracteres supera el límite de 100 para este KEY.",
    SOBRAN_CARACTERES_255: "La cantidad de caracteres supera el límite de 255 para este KEY.",
    SOBRAN_CARACTERES_10: "La cantidad de caracteres supera el límite de 10 para este KEY.",
    SOBRAN_CARACTERES_2: "La cantidad de caracteres supera el límite de 2 para este KEY.",
    SOBRAN_CARACTERES_20: "La cantidad de caracteres supera el límite de 20 para este KEY.",
    SOBRAN_CARACTERES_1: "La cantidad de caracteres supera el límite de 1 para este KEY.",
    SOBRAN_CARACTERES_120: "La cantidad de caracteres supera el límite de 120 para este KEY.",
    SOBRAN_CARACTERES_30: "La cantidad de caracteres supera el límite de 30 para este KEY.",
    SOBRAN_CARACTERES_50: "La cantidad de caracteres supera el límite de 50 para este KEY.",
    FALTAN_CARACTERES: "La cantidad de caracteres es menor a lo permitido.",
    EMAIL_INCORRECTO: "La estructura del email es incorrecta. No puede tener espacios y debe contener un '@'.",
    EMAIL_NO_EXISTE: "El email ingresado no existe.",
    TELEFONO_INCORRECTO: "La estructura del teléfono es incorrecta. No puede contener letras ni espacios y su tamaño maximo es de 20.",
    KEY_NO_EXISTE: "El valor proporcionado no se encuentra entre los valores aceptados. Verifique la documentación de esta función.",
    CARACTER_INVALIDO: "Uno o varios caracteres ingresados son inválidos para este campo.",
    COUNTRY_NO_EXISTE: "El código alfa-2 ingresado no existe. Verifique la tabla de paises e ingrese el código que corresponda.",
    TIMEZONE_NO_EXISTE: "El valor de timezone ingresado no existe. Verifique la tabla de zonas horarias e ingrese el valor que corresponda.",
    IDNUMBER_INCORRECTO: "La estructura del idnumber no cumple con los parámetros. Verifique la documentación de esta función",
    USERNAME_INCORRECTO: "La estructura del username no cumple con los parámetros. Verifique la documentación de esta función",
    LANG_NO_EXISTE: "El lenguaje ingresado no existe. Verifique la tabla de lenguas aceptadas en la documentación de esta función.",
    NO_ENCONTRADO: "El dato consultado no existe en la base de datos.",
    CARACTER_INVALIDO_USERNAME: "La estructura del username es incorrecta. Solo se permiten caracteres alfanuméricos con letras minúsculas, guion bajo (_), guion (-), punto (.) y el símbolo de arroba (@). Su longitud no puede superar los 100 caracteres.",
    CARACTER_INVALIDO_EMAIL: "La estructura del email es incorrecta. No se permiten espacios y debe contener un '@'",
    CARACTER_INVALIDO_ID: "La estructura del id es incorrecta. No se permiten letras, espacios ni números negativos.",
    QUIZ_NO_EXISTE: "El quiz consultado no existe.",
    COURSE_NO_EXISTE: "El curso consultado no existe.",
    USER_NO_EXISTE: "El usuario consultado no existe",
    GROUP_NO_EXISTE: "El grupo consultado no existe.",
    USUARIO_AÑADIDO: "El usuario fue añadido correctamente al grupo.",
    GRUPO_AÑADIDO: "El grupo fue creado correctamente.",
    GRUPO_YA_EXISTE: "El grupo ya existe en ese curso.",
    ASSIGNMENT_NO_EXISTE: "El assignment consultado no existe.",
    NO_MATRICULA_MANUAL: "La matrícula manual esta deshabilitada para este curso.",
    NO_INFORMACION: "No hay información para mostrar en la base de datos.",
    ACTION_NO_EXISTE: "La acción consultada no existe.",
    USUARIO_NO_MATRICULADO: "El usuario no se encuentra matriculado en este curso.",
    DATOS_INVALIDOS: "Ingrese el valor de username o el email. No ingrese ambos datos.",
    CAMBIO_CONTRASEÑA: "Se envió un correo electrónico, este contiene instrucciones sencillas para confirmar y completar este cambio de contraseña. Si sigue teniendo problemas, por favor contacte con el administrador del sitio.",
    ERROR_LOG: "El username o el password estan incorrectos. Verifique los datos.",
    NO_BADGES: "El usuario no tiene insignias para mostrar.",
    EVENTO_NO_EXISTE: "El evento ingresado no existe.",
    SIN_PERMISOS: "No tiene permisos en el sistema para realizar esta operación.",
    CONTEXT_NO_EXISTE: "El contexto ingresado no existe.",
    TOUR_NO_EXISTE: "El tour ingresado no existe.",
    URL_NO_LOCAL: "La url ingresada no es local.",
    IDNUMBER_VALOR_CAT_MAL: "El valor del idnumber o el de la categoría son incorrectos."
}

"""
 ## **Códigos retornados:**
        - 200 -> La operación se realizó correctamente.
        - 452 -> La cantidad de caracteres supera el límite de 100 para este KEY.
        - 453 -> La cantidad de caracteres supera el límite de 255 para este KEY.
        - 454 -> La cantidad de caracteres supera el límite de 10 para este KEY.
        - 455 -> La cantidad de caracteres supera el límite de 2 para este KEY.
        - 456 -> La cantidad de caracteres supera el límite de 20 para este KEY.
        - 457 -> La cantidad de caracteres supera el límite de 1 para este KEY.
        - 458 -> La cantidad de caracteres supera el límite de 120 para este KEY.
        - 459 -> La cantidad de caracteres supera el límite de 30 para este KEY.
        - 460 -> La cantidad de caracteres es menor a lo permitido.
        - 461 -> La estructura del email es incorrecta. No puede tener espacios y debe contener un '@'.
        - 462 -> El email ingresado no existe.
        - 463 -> La estructura del teléfono es incorrecta. No puede contener letras ni espacios y su tamaño máximo es de 20.
        - 464 -> El valor proporcionado no se encuentra entre los valores aceptados. Verifique la documentación de esta función.
        - 465 -> Uno o varios caracteres ingresados son inválidos para este campo.
        - 466 -> El código alfa-2 ingresado no existe. Verifique la tabla de países e ingrese el código que corresponda.
        - 467 -> El valor de timezone ingresado no existe. Verifique la tabla de zonas horarias e ingrese el valor que corresponda.
        - 468 -> La estructura del idnumber no cumple con los parámetros. Verifique la documentación de esta función.
        - 469 -> La estructura del username no cumple con los parámetros. Verifique la documentación de esta función.
        - 470 -> El lenguaje ingresado no existe. Verifique la tabla de lenguas aceptadas en la documentación de esta función.
        - 471 -> El dato consultado no existe en la base de datos.
        - 472 -> La estructura del username es incorrecta. Solo se permiten caracteres alfanuméricos con letras minúsculas, guion bajo (_), guion (-), punto (.) y el símbolo de arroba (@). Su longitud no puede superar los 100 caracteres.
        - 473 -> La estructura del email es incorrecta. No se permiten espacios y debe contener un '@'.
        - 474 -> La estructura del id es incorrecta. No se permiten letras, espacios ni números negativos.
        - 475 -> La cantidad de caracteres supera el límite de 50 para este KEY.
        - 476 -> El quiz consultado no existe.
        - 477 -> El curso consultado no existe.
        - 478 -> El usuario consultado no existe.
        - 479 -> El grupo consultado no existe.
        - 480 -> El usuario fue añadido correctamente al grupo.
        - 481 -> El grupo fue creado correctamente.
        - 482 -> El grupo ya existe en ese curso.
        - 483 -> El assignment consultado no existe.
        - 484 -> La matrícula manual esta deshabilitada para este curso.
        - 485 -> No hay información para mostrar en la base de datos.
        - 486 -> La acción consultada no existe.
        - 487 -> El usuario no se encuentra matriculado en este curso.
        - 488 -> Ingrese el valor de username o el email. No complete ambos campos, solamente uno.
        - 489 -> Se envió un correo electrónico, este contiene instrucciones sencillas para confirmar y completar este cambio de contraseña. Si sigue teniendo problemas, por favor contacte con el administrador del sitio.
        - 490 -> El username o el password estan incorrectos. Verifique los datos.
        - 491 -> El usuario no tiene insignias para mostrar.
        - 492 -> El evento ingresado no existe.
        - 493 -> No tiene permisos en el sistema para realizar esta operación.
        - 494 -> El contexto ingresado no existe.
        - 495 -> El tour ingresado no existe.
        - 496 -> La url ingresada no es local.
        - 497 -> El valor del idnumber o el de la categoría son incorrectos.
        
"""

