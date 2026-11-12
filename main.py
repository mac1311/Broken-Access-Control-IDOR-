from fastapi import FastAPI, Depends, HTTPException,Header,status
from sqlalchemy import create_engine,Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, Session

#Url de conexión
DATABASE_URL= "sqlite:///./pedidos.db"
#Motor de conexión
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
#Fábrica de sesiones 
SessionLocal = sessionmaker(autocommit=False,autoflush=False,bind=engine)

Base = declarative_base()

class Usuario(Base):
    __tablename__ = "usuarios"
    id =Column(Integer,primary_key=True,index=True)
    nombre = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)

class Pedido(Base):
    __tablename__ = "pedidos"
    id = Column(Integer, primary_key=True, index=True)
    descripcion = Column(String, nullable=False)
    total = Column(Float, nullable=False)
    dueno_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

Base.metadata.create_all(bind=engine)

def seed_data():
    db = SessionLocal()
    if not db.query(Usuario).first():
        alice = Usuario(id=1,nombre="Alice",email="alice@test.com")
        bob = Usuario(id=2, nombre = "Bob", email = "bob@test.com")
        db.add_all([alice,bob])
        db.commit()

        pedido_alice = Pedido(id=1, descripcion="Notebook Dell XPS (Confidencial)", total=2500000.0, dueno_id=1)
        pedido_bob = Pedido(id=2, descripcion="Mouse USB", total=20000.0, dueno_id=2)
        db.add_all([pedido_alice, pedido_bob])
        db.commit()
    db.close()

seed_data()

app = FastAPI(title="Ejemplo Broken Access Control (IDOR)")

@app.get("/vulnerable/pedidos/{pedido_id}")
def ver_pedido_vulnerable(pedido_id: int, db: Session = Depends(get_db)):
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return {
        "id": pedido.id,
        "descripcion": pedido.descripcion,
        "total": pedido.total,
        "dueno_id": pedido.dueno_id,
    }


def usuario_actual(x_usuario_id: int = Header(...), db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.id == x_usuario_id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no autenticado o no existe"
        )
    return usuario

@app.get("/seguro/pedidos/{pedido_id}")
def ver_pedido_seguro(
    pedido_id: int, 
    usuario: Usuario = Depends(usuario_actual), 
    db: Session = Depends(get_db)
):
    pedido = db.query(Pedido).filter(
        Pedido.id == pedido_id,
        Pedido.dueno_id == usuario.id
    ).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return {
        "id": pedido.id,
        "descripcion": pedido.descripcion,
        "total": pedido.total,
        "dueno_id": pedido.dueno_id,
    }