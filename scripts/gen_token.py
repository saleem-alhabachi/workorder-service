from app.core.security import create_token

print("EDITOR TOKEN:\n", create_token("saleem-alhabachi", role="editor"))
print("\nVIEWER TOKEN:\n", create_token("viewer-1", role="viewer"))
