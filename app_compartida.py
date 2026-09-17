import flet as ft
import requests

# URL de tu base de datos en Firebase
FIREBASE_URL = "https://listacompracasa-default-rtdb.firebaseio.com/lista_compra"

def main(page: ft.Page):
    page.title = "Lista de la Compra Compartida"
    page.padding = 20
    page.theme_mode = ft.ThemeMode.LIGHT
    
    # Estado del usuario actual (por defecto Juan)
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

    # Selector de usuario (configurado de forma compatible con Flet moderno)
    dropdown_usuario = ft.Dropdown(
        value="Juan",
        width=120,
        options=[
            ft.dropdown.Option("Juan"),
            ft.dropdown.Option("Gema"),
        ]
    )
    # Asignamos el evento on_change fuera del constructor para evitar el error
    dropdown_usuario.on_change = cambiar_usuario

    def cargar_datos_desde_nube():
        """Lee los datos en tiempo real desde Firebase."""
        columna_lista.controls.clear()
        try:
            res = requests.get(f"{FIREBASE_URL}.json")
            datos = res.json() if res.status_code == 200 else {}
        except Exception as err:
            datos = {}
            print(f"Error de conexión: {err}")

        hay_pendientes = False
        if datos:
            for clave, prod in datos.items():
                if isinstance(prod, dict) and not prod.get("comprado", False):
                    hay_pendientes = True
                    
                    def al_marcar(e, key=clave):
                        requests.patch(f"{FIREBASE_URL}/{key}.json", json={"comprado": True})
                        cargar_datos_desde_nube()

                    item = ft.Container(
                        content=ft.Row([
                            ft.Checkbox(
                                label=f"{prod.get('nombre')} (añadido por {prod.get('usuario')})",
                                on_change=al_marcar,
                                expand=True
                            )
                        ]),
                        padding=10,
                        bgcolor=ft.Colors.GREY_100,
                        border_radius=8
                    )
                    columna_lista.controls.append(item)

        if not hay_pendientes:
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

    # Cabecera con selector de usuario
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
    import os
    port = int(os.environ.get("PORT", 8000))
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, host="0.0.0.0", port=port)
