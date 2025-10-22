try:
    import pkgutil
    import adobe.pdfservices.operation
    
    print("Adobe PDF Services SDK modules:")
    for importer, modname, ispkg in pkgutil.walk_packages(adobe.pdfservices.operation.__path__, adobe.pdfservices.operation.__name__ + '.'):
        print(f"  {modname}")
except Exception as e:
    print(f"Error: {e}")
    
# Check specific imports
try:
    from adobe.pdfservices.operation.pdf_services import PDFServices
    print("✓ PDFServices import successful")
except Exception as e:
    print(f"✗ PDFServices import failed: {e}")

try:
    from adobe.pdfservices.operation.auth.service_principal_credentials import ServicePrincipalCredentials
    print("✓ ServicePrincipalCredentials import successful")
except Exception as e:
    print(f"✗ ServicePrincipalCredentials import failed: {e}")

try:
    from adobe.pdfservices.operation.pdfjobs.params.export_pdf.export_pdf_params import ExportPDFParams
    print("✓ ExportPDFParams import successful")
except Exception as e:
    print(f"✗ ExportPDFParams import failed: {e}")

try:
    from adobe.pdfservices.operation.pdfjobs.params.export_pdf.export_pdf_target_format import ExportPDFTargetFormat
    print("✓ ExportPDFTargetFormat import successful")
except Exception as e:
    print(f"✗ ExportPDFTargetFormat import failed: {e}")

try:
    from adobe.pdfservices.operation.pdfjobs.jobs.export_pdf_job import ExportPDFJob
    print("✓ ExportPDFJob import successful")
except Exception as e:
    print(f"✗ ExportPDFJob import failed: {e}")

try:
    from adobe.pdfservices.operation.io.cloud_asset import CloudAsset
    print("✓ CloudAsset import successful")
except Exception as e:
    print(f"✗ CloudAsset import failed: {e}")

try:
    from adobe.pdfservices.operation.io.stream_asset import StreamAsset
    print("✓ StreamAsset import successful")
except Exception as e:
    print(f"✗ StreamAsset import failed: {e}")