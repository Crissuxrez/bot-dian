"""
Interfaz por línea de comandos para el Agente de Soporte DIAN
Uso: python cli.py [archivo.xml]
"""
import sys
import argparse
from pathlib import Path
from src.agent import DianSupportAgent
from src.config import MANUALES_DIR, EJEMPLOS_DIR


def main():
    parser = argparse.ArgumentParser(description="Agente de Soporte Técnico DIAN")
    parser.add_argument("file", nargs="?", help="Archivo XML a analizar")
    parser.add_argument("--load-manuals", action="store_true", help="Cargar manuales desde data/manuales")
    parser.add_argument("--list", action="store_true", help="Listar documentos cargados")
    parser.add_argument("--clear", action="store_true", help="Limpiar base de conocimiento")
    
    args = parser.parse_args()
    
    print("🤖 Inicializando Agente de Soporte DIAN...")
    agent = DianSupportAgent()
    print(f"✅ Agente listo. Documentos en KB: {agent.knowledge_manager.count()}")
    
    if args.clear:
        print("⚠️ Esta opción no está implementada completamente.")
        print("Para limpiar manualmente, elimina la carpeta knowledge_base/")
        return
    
    if args.list:
        docs = agent.list_manuals()
        if docs:
            print("\n📚 Documentos en la base de conocimiento:")
            for doc in docs:
                print(f"  - {doc['filename']} ({doc['type']})")
        else:
            print("\n📚 No hay documentos cargados.")
        return
    
    if args.load_manuals:
        print(f"\n📂 Cargando manuales desde {MANUALES_DIR}...")
        results = agent.load_manuals_from_folder(str(MANUALES_DIR))
        for filename, success in results.items():
            status = "✅" if success else "❌"
            print(f"  {status} {filename}")
        print(f"\nTotal documentos en KB: {agent.knowledge_manager.count()}")
        return
    
    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"❌ Archivo no encontrado: {file_path}")
            return
        
        print(f"\n📄 Analizando: {file_path.name}")
        
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        file_type = "xml" if file_path.suffix.lower() == '.xml' else "txt"
        analysis = agent.analyze_document(content, file_type, file_path.name)
        
        print("\n" + "="*60)
        if analysis['success']:
            print("✅ ANÁLISIS COMPLETADO - Sin errores críticos")
        else:
            print("❌ ERRORES DETECTADOS")
        print("="*60)
        
        if analysis.get('errors'):
            print("\n📋 Errores:")
            for error in analysis['errors']:
                print(f"  ❌ {error}")
        
        if analysis.get('recommendations'):
            print("\n✅ Recomendaciones:")
            for rec in analysis['recommendations']:
                print(f"  🔧 {rec}")
        
        if analysis.get('summary'):
            print("\n💰 Resumen de totales:")
            s = analysis['summary']
            print(f"  Subtotal: ${s.get('line_extension', 0):,.0f}")
            print(f"  IVA: ${s.get('iva_declared', 0):,.0f}")
            print(f"  ReteFuente: ${s.get('rete_fuente_declared', 0):,.0f}")
            print(f"  ReteIVA: ${s.get('rete_iva_declared', 0):,.0f}")
            print(f"  Total: ${s.get('payable', 0):,.0f}")
        
        return
    
    # Modo interactivo
    print("\n💬 Modo interactivo. Escribe 'salir' para terminar.\n")
    
    while True:
        try:
            user_input = input("👤 Tú: ").strip()
            if user_input.lower() in ['salir', 'exit', 'quit']:
                break
            if not user_input:
                continue
            
            # Analizar si parece XML
            if "<xml" in user_input.lower() or "<?xml" in user_input:
                analysis = agent.analyze_document(user_input, "xml", "input")
                response = agent.generate_response(user_input, analysis)
            else:
                response = agent.generate_response(user_input)
            
            print(f"\n🤖 Agente:\n{response}\n")
            
        except KeyboardInterrupt:
            print("\n\n👋 Hasta luego!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()