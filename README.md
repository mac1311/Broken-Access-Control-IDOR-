# Laboratorio: Broken Access Control (IDOR)
**Materia:** Desarrollo 3 — Semestre 7  
**Tema:** OWASP Top 10 — A01:2021 Broken Access Control (Insecure Direct Object Reference)

---

## 1. Fundamentos Teóricos

### Autenticación vs. Autorización
* **Autenticación (¿Quién sos?):** Comprueba la identidad del usuario (ej. credenciales, tokens JWT o sesión).
* **Autorización (¿Qué podés hacer?):** Verifica si el usuario autenticado tiene permisos sobre el recurso específico que solicita.

### ¿Qué es IDOR?
**Insecure Direct Object Reference (IDOR)** ocurre cuando una aplicación expone una referencia directa a un objeto interno (como un ID de base de datos en la URL) y **no valida si el usuario solicitante es el legítimo propietario o tiene privilegios para acceder a dicho objeto**.

---

## 2. Comparativa de Código

### Endpoint Vulnerable
```python
@app.get("/vulnerable/pedidos/{pedido_id}")
def ver_pedido_vulnerable(pedido_id: int, db: Session = Depends(get_db)):
    # ERROR: Busca el ID a ciegas. Cualquier cliente puede ver registros de otros.
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return pedido
```

### Endpoint Protegido (Mitigación)
```python
@app.get("/seguro/pedidos/{pedido_id}")
def ver_pedido_seguro(
    pedido_id: int,
    usuario: Usuario = Depends(usuario_actual),  # 1. Autenticación
    db: Session = Depends(get_db)
):
    # 2. Autorización: Se filtra explícitamente por el dueño del recurso
    pedido = db.query(Pedido).filter(
        Pedido.id == pedido_id,
        Pedido.dueno_id == usuario.id            # <-- Control de acceso
    ).first()
    
    if not pedido:
        # Prevención de enumeración de IDs
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return pedido
```

> **Decisión de Seguridad (404 vs 403):** Se devuelve `404 Not Found` en lugar de `403 Forbidden` para evitar que un atacante descubra qué IDs existen mediante enumeración ciega.

---

## 3. Estructura del Proyecto

```text
broken_acces_control/
├── main.py        # API FastAPI con modelos, seed data y endpoints
├── test_lab.py    # Script de prueba automatizada en consola
├── pedidos.db     # Base de datos SQLite (se genera automáticamente)
└── README.md      # Documentación y justificación técnica
```

---

## 4. Datos Precargados para Pruebas

| ID Usuario | Nombre | Rol / Contexto | Pedido Asignado |
| :--- | :--- | :--- | :--- |
| `1` | **Alice** | Usuaria legítima | Pedido `#1`: *Notebook Dell Latitude Pro* ($2500) |
| `2` | **Bob** | Atacante potencial | Pedido `#2`: *Teclado USB básico* ($25) |

---

## 5. Instrucciones de Ejecución

### Opción A: Prueba Rápida en Terminal
Ejecuta los escenarios de prueba directamente sin necesidad de levantar el navegador:
```powershell
.\venv\Scripts\python.exe test_lab.py
```

### Opción B: Interfaz Interactiva Swagger UI
1. Iniciar el servidor:
   ```powershell
   fastapi dev main.py
   ```
2. Abrir en el navegador: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
3. Probar los casos:
   - **Caso Vulnerable:** `GET /vulnerable/pedidos/1` (devuelve los datos confidenciales de Alice sin pedir autenticación).
   - **Caso Seguro (Ataque detenido):** `GET /seguro/pedidos/1` con header `x-usuario-id: 2` (Bob recibe `404 Not Found`).
   - **Caso Seguro (Acceso permitido):** `GET /seguro/pedidos/1` con header `x-usuario-id: 1` (Alice accede a su pedido legítimamente).

