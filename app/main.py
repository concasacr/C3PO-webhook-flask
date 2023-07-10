from app import servicio_whatsapp
import multiprocessing

def main():
    p1 = multiprocessing.Process(target=servicio_whatsapp.start_whatsapp_service)
    p1.start()

if __name__ == '__main__':
    main()
