import flet as ft
import requests
import os

FIREBASE_URL = "https://listacompracasa-default-rtdb.firebaseio.com/lista_compra"

def main(page: ft.Page):
    page.title = "Lista de la Compra Compartida"
    page.padding = 20
    page.theme_mode = ft.ThemeMode.LIGHT
    
    state_usuario = {"nombre": "Juan"}

    input_producto = ft.TextField(
        hint_text="Añadir producto (ej: Fregasuelos)...",
        expand=True
    )
    columna_lista = ft.Column(scroll=ft.ScrollMode.AUTO)

    def cambiar_usuario(e):
        state_usuario["nombre"] = dropdown_usuario.value
        page.snack_bar = ft.SnackBar(ft.Text(f"Modo cambiado a: {state_usuario['nombre']}"))
        page.snack_bar.open = True
        page.update()

    dropdown_usuario = ft.Dropdown(
        value="Juan",
        width=120,
        options=[
            ft.dropdown.Option("Juan"),
            ft.dropdown.Option("Gema"),
            ft.dropdown.Option("Aarón"),
            ft.dropdown.Option("Dylan"),
        ]
    )
    dropdown_usuario.on_change = cambiar_usuario

    def cargar_datos_desde_nube():
        columna_lista.controls.clear()
        try:
            res = requests.get(f"{FIREBASE_URL}.json")
            datos = res.json() if res.status_code == 200 else {}
        except Exception as err:
            datos = {}
            print(f"Error de conexión: {err}")

        hay_items = False
        if datos and isinstance(datos, dict):
            for clave, prod in datos.items():
                if isinstance(prod, dict):
                    hay_items = True
                    comprado = prod.get("comprado", False)
                    nombre_prod = prod.get("nombre", "")
                    usuario_prod = prod.get("usuario", "")

                    # Tachar texto e inclinar si está comprado
                    estilo_texto = ft.TextStyle(
                        decoration=ft.TextDecoration.LINE_THROUGH, 
                        color="grey",
                        italic=True
                    ) if comprado else None

                    def al_comprobar(e, key=clave, estado_actual=comprado):
                        requests.patch(f"{FIREBASE_URL}/{key}.json", json={"comprado": not estado_actual})
                        cargar_datos_desde_nube()

                    def al_borrar(e, key=clave):
                        requests.delete(f"{FIREBASE_URL}/{key}.json")
                        cargar_datos_desde_nube()

                    item = ft.Container(
                        content=ft.Row([
                            ft.Checkbox(
                                value=comprado,
                                on_change=al_comprobar
                            ),
                            ft.Text(
                                f"{nombre_prod} (añadido por {usuario_prod})",
                                style=estilo_texto,
                                expand=True
                            ),
                            ft.IconButton(
                                icon=ft.Icons.DELETE_OUTLINE,
                                icon_color=ft.Colors.RED_400,
                                tooltip="Eliminar producto",
                                on_click=al_borrar
                            )
                        ]),
                        padding=5,
                        bgcolor=ft.Colors.GREY_100 if not comprado else ft.Colors.GREY_200,
                        border_radius=8
                    )
                    columna_lista.controls.append(item)

        if not hay_items:
            columna_lista.controls.append(
                ft.Text("¡Lista vacía! No hay nada pendiente.", color="grey", italic=True)
            )
        page.update()

    def agregar_click(e):
        texto = input_producto.value.strip().capitalize()
        if texto:
            nuevo_item = {
                "nombre": texto,
                "usuario": state_usuario["nombre"],
                "comprado": False
            }
            requests.post(f"{FIREBASE_URL}.json", json=nuevo_item)
            input_producto.value = ""
            cargar_datos_desde_nube()

    btn_refrescar = ft.IconButton(
        icon=ft.Icons.REFRESH, 
        tooltip="Actualizar lista",
        on_click=lambda e: cargar_datos_desde_nube()
    )

    page.add(
        ft.Row([
            ft.Text("🛒 Lista de la Compra", size=22, weight=ft.FontWeight.BOLD, expand=True),
            dropdown_usuario,
            btn_refrescar
        ]),
        ft.Divider(),
        ft.Row([
            input_producto,
            ft.IconButton(icon=ft.Icons.ADD_CIRCLE, icon_size=36, icon_color=ft.Colors.BLUE_600, on_click=agregar_click)
        ]),
        columna_lista
    )

    cargar_datos_desde_nube()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    ft.app(target=main, port=port)
