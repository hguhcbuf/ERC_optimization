class Parameter {
  final String name;
  final double min;
  final double max;

  Parameter({required this.name, required this.min, required this.max});

  Map<String, dynamic> toJson() => {'name': name, 'min': min, 'max': max};
}
